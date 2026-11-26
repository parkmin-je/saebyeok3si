"""감정 연기 목소리: Gemini 무료 TTS.

- 이어지는 대사를 화자 2명 이하·5줄 이하로 묶어 한 번에 연기시킨다 (편당 요청 5~6번, 무료 한도 안).
- 줄마다 "how" (감정 지시)를 괄호로 넣는다. 속마음(inner) 줄은 채널 설정의 지시가 앞에 붙는다.
- 묶음 녹음은 Gemini Flash(텍스트 모델, 다른 무료 한도)에게 들려서 줄마다 시작·끝을 받아 자른다.
  길이가 이상한 줄만 따로 다시 녹음한다.
- 키는 환경 변수 GEMINI_API_KEY 로만 받는다 (저장소·로그에 남기지 않는다).
- --fake-voice 면 네트워크 없이 길이만 맞춘 삐 소리를 만든다 (길이·자막 확인용).
"""

import base64
import difflib
import hashlib
import io
import itertools
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

import numpy as np

from .timeline import plain

SR = 24000  # Gemini TTS 출력
# 무료 한도는 모델마다 따로 (하루 약 10회씩). 앞 모델이 바닥나면 다음 모델로 넘어간다.
TTS_MODELS = os.environ.get(
    "GEMINI_TTS_MODELS", "gemini-3.8-flash-tts,gemini-3.1-flash-tts-preview,gemini-2.5-flash-preview-tts,gemini-3.8-flash-lite-tts"
).split(",")
_spent: set[str] = set()  # 이번 실행에서 하루 한도가 끝난 모델
ALIGN_MODELS = os.environ.get(
    "GEMINI_ALIGN_MODELS",
    "gemini-3.5-flash,gemini-2.5-flash,gemini-3.8-flash,gemini-3-flash-preview,gemini-3.7-flash,gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite",
).split(",")
API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
WAIT = 21  # 무료 등급 분당 3회
FAKE_CPS = 6.5


class VoiceError(RuntimeError):
    pass


# ---------- 파일 ----------
def key_of(ep, ln) -> str:
    v = ep["gvoices"][ln["who"]]
    return hashlib.sha1(f"{v}|{ln['who']}|{plain(ln['text'])}|{ln.get('how', '')}".encode()).hexdigest()[:12]


def path_of(ep, work, ln, fake=False) -> Path:
    return Path(work) / "voice" / f"{'fake' if fake else 'g'}-{ln['who']}-{key_of(ep, ln)}.wav"


def read_wav(path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as f:
        x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
        return x, f.getframerate()


def wav_bytes(y, sr=SR) -> bytes:
    b = io.BytesIO()
    with wave.open(b, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    return b.getvalue()


def write_wav(path, y, sr=SR) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(wav_bytes(y, sr))


def length(path) -> float:
    with wave.open(str(path)) as f:
        return f.getnframes() / f.getframerate()


def fresh(out: Path, src: Path) -> bool:
    """만들어 둔 사본이 원본보다 새것인가 (원본을 다시 녹음하면 사본도 다시 만든다)."""
    return out.exists() and out.stat().st_mtime >= src.stat().st_mtime


def with_fx(ep, path: Path, who: str) -> Path:
    """ep["fx"][who] = 음높이 배수 (예: 1.15) 면 높고 귀여운 목소리로 바꾼 사본을 쓴다."""
    k = ep.get("fx", {}).get(who)
    if not k:
        return path
    out = path.with_name(path.stem + f"-fx{k}.wav")
    if not fresh(out, path):
        _, sr = read_wav(path)
        tempo = 1 / k * ep.get("fxtempo", {}).get(who, 1.08)
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-i",
                str(path),
                "-af",
                f"asetrate={int(sr * k)},aresample={sr},atempo={tempo:.4f},equalizer=f=3000:t=q:w=1:g=3,volume=1.1",
                str(out),
            ],
            check=True,
        )
    return out


def tighten(x, max_gap=0.22) -> np.ndarray:
    """줄 안의 긴 쉼(0.3초 넘는 것)을 max_gap 초로 줄인다. 쇼츠는 숨 돌릴 틈이 짧아야 한다."""
    segs = segments(x, min_gap=0.3)
    if len(segs) < 2:
        return x
    keep = int(max_gap * SR)
    out = [x[: int(segs[0][1] * SR)]]
    for (_, b), (a2, b2) in itertools.pairwise(segs):
        gap = x[int(b * SR) : int(a2 * SR)]
        out += [gap[: keep // 2], gap[-(keep - keep // 2) :], x[int(a2 * SR) : int(b2 * SR)]]
    out.append(x[int(segs[-1][1] * SR) :])
    return np.concatenate(out)


def with_speed(ep, path: Path) -> Path:
    """줄 안 쉼을 줄이고, ep["speed"] (예: 1.08) 만큼 빠르게 (음높이는 그대로)."""
    sp = ep.get("speed", 1.0)
    out = path.with_name(path.stem + f"-t{sp}.wav")
    if fresh(out, path):
        return out
    x, sr = read_wav(path)
    tmp = path.with_name(path.stem + "-tight.wav")
    write_wav(tmp, tighten(x) if sr == SR else x, sr)
    if sp == 1.0:
        tmp.replace(out)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", f"atempo={sp}", str(out)], check=True)
        tmp.unlink()
    return out


def final_path(ep, work, ln, fake=False) -> Path:
    p = path_of(ep, work, ln, fake)
    return with_fx(ep, p if fake else with_speed(ep, p), ln["who"])


# ---------- 묶기 ----------
def groups(lines, max_lines=5) -> list[list[dict]]:
    """이어지는 줄을 화자 2명 이하·max_lines 줄 이하 묶음으로 나눈다."""
    out, cur = [], []
    for ln in lines:
        names = {x["who"] for x in cur} | {ln["who"]}
        if cur and (len(names) > 2 or len(cur) >= max_lines):
            out.append(cur)
            cur = []
        cur.append(ln)
    if cur:
        out.append(cur)
    return out


def label(ep, who) -> str:
    return re.sub(r"[\s()]", "", ep.get("names", {}).get(who, who)) or who


def speak(text: str) -> str:
    """TTS 에 보낼 글자. 앞뒤 말줄임표는 빼고(앞에 오면 수십 초 침묵·헛소리가 남) 가운데 것은 쉼표로."""
    t = re.sub(r"^[….\s]+|[…\s]+$", "", plain(text))
    return re.sub(r"\s*…+\s*", ", ", t)


def tts_body(ep, grp, model="") -> dict:
    spk = list(dict.fromkeys(ln["who"] for ln in grp))
    cast = ep.get("gcast", {})
    head = ep.get("gdirect", "") + "\n" + "\n".join(f"- {label(ep, w)}: {cast.get(w, '')}" for w in spk)
    body = "\n".join(f"{label(ep, ln['who'])}: ({ln.get('how', '자연스럽게')}) {speak(ln['text'])}" for ln in grp)
    prompt = (
        f"{head}\n대사마다 감정을 크게 살려 연기하고, 대사와 대사 사이는 반드시 2초 동안 완전히 조용히 쉬세요. "
        f"괄호 안 지시는 읽지 마세요.\n\n{body}"
    )
    if len(spk) == 1:
        sc = {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": ep["gvoices"][spk[0]]}}}
    else:
        sc = {
            "multiSpeakerVoiceConfig": {
                "speakerVoiceConfigs": [
                    {"speaker": label(ep, w), "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": ep["gvoices"][w]}}} for w in spk
                ]
            }
        }
    parts = [{"text": prompt}]
    if model.startswith("gemini-3.8") and len(spk) == 1:
        # 3.8 계열은 긴 지시문을 그대로 읽어 버린다 → [감정] 태그만
        parts = [{"text": " ".join(f"[{ln.get('how', '자연스럽게')}] {speak(ln['text'])}" for ln in grp)}]
    elif model.startswith("gemini-3.8"):
        # 3.8 계열은 여러 명일 때 줄마다 화자를 붙여야 하고, 지시문은 [감정] 태그로만 받는다
        parts = [
            {"text": f"[{ln.get('how', '자연스럽게')}] {speak(ln['text'])}", "speechMetadata": {"speaker": label(ep, ln["who"])}}
            for ln in grp
        ]
    return {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": sc}}


def _post(model, body) -> dict:
    req = urllib.request.Request(
        API.format(model),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def _redact(msg: str) -> str:
    return re.sub(r"AIza[0-9A-Za-z_-]+", "***", msg)


def decode(part) -> np.ndarray:
    """inlineData 를 24kHz float 로. 모델에 따라 raw PCM 또는 WAV 로 온다."""
    a = base64.b64decode(part["data"])
    if a[:4] == b"RIFF":
        with wave.open(io.BytesIO(a)) as w:
            if w.getframerate() != SR or w.getsampwidth() != 2:
                raise VoiceError(f"예상 밖 오디오 형식 {w.getframerate()}Hz/{w.getsampwidth()}B")
            a = w.readframes(w.getnframes())
    return np.frombuffer(a, dtype=np.int16).astype(np.float32) / 32768


def request(ep, grp, log=print) -> np.ndarray:
    """묶음 하나를 녹음한다 (24kHz float). 모델 한도가 끝나면 다음 모델로."""
    for model in TTS_MODELS:
        if model in _spent:
            continue
        body = tts_body(ep, grp, model)
        for k in range(4):
            try:
                d = _post(model, body)
                return decode(d["candidates"][0]["content"]["parts"][0]["inlineData"])
            except urllib.error.HTTPError as e:
                full = e.read().decode()
                msg = full[:400]
                if (e.code == 429 and ("PerDay" in full or "free_tier" in full)) or e.code in (400, 404):
                    _spent.add(model)
                    log(f"{model}: 쓸 수 없음 ({e.code}), 다음 모델로")
                    break
                if e.code in (429, 500, 503) and k < 3:
                    time.sleep(30 * (k + 1))
                    continue
                raise VoiceError(f"Gemini TTS 실패 {e.code}: {_redact(msg)}") from None
            except (KeyError, IndexError, TimeoutError, urllib.error.URLError) as e:
                if k < 2:
                    time.sleep(10)
                    continue
                log(f"{model}: 응답 없음 ({type(e).__name__}), 다음 모델로")
                break
    raise VoiceError("무료 TTS 모델 한도가 모두 끝남 (내일 다시)")


# ---------- 자르기 ----------
def envelope(x, hop) -> np.ndarray:
    n = max(1, (len(x) - hop) // hop + 1)
    return np.array([np.abs(x[i * hop : i * hop + hop]).max() for i in range(n)])


def trim(x) -> np.ndarray:
    """앞뒤 무음을 자르고 조금 여유를 둔다 (한 줄 녹음용)."""
    hop = int(SR * 0.02)
    env = envelope(x, hop)
    loud = np.nonzero(env >= max(0.015, env.max() * 0.03))[0]
    if not len(loud):
        return x
    a, b = loud[0] * hop, loud[-1] * hop + hop
    return x[max(0, a - 2400) : b + 4800]


def segments(x, min_gap=0.26) -> list[tuple[float, float]]:
    """소리 덩어리 (min_gap초 이상 쉼으로 나눈 구간) 목록, 초 단위."""
    hop = int(SR * 0.02)
    env = envelope(x, hop)
    loud = env >= max(0.015, env.max() * 0.03)
    segs, s, e, gap = [], None, 0, 0
    for i, v in enumerate(loud):
        if v:
            if s is None:
                s = i
            gap, e = 0, i
        elif s is not None:
            gap += 1
            if gap * 0.02 >= min_gap:
                segs.append((s * hop / SR, (e + 1) * hop / SR))
                s = None
    if s is not None:
        segs.append((s * hop / SR, (e + 1) * hop / SR))
    return segs


def assign(x, marks: dict[int, tuple[float, float]], n: int) -> list[np.ndarray | None]:
    """소리 덩어리를 가장 많이 겹치는 줄(marks: 줄번호 → (시작, 끝))에 붙여 줄마다 잘라 낸다. 빠진 줄은 None."""
    own: dict[int, list[tuple[float, float]]] = {}
    for a, b in segments(x):
        best, bi = 0.0, None
        for i, (ms, me) in marks.items():
            ov = min(b, me + 0.2) - max(a, ms - 0.2)
            if ov > best:
                best, bi = ov, i
        if bi is not None:
            own.setdefault(bi, []).append((a, b))
    out = []
    for i in range(n):
        if i not in own:
            out.append(None)
            continue
        a, b = own[i][0][0], own[i][-1][1]
        out.append(x[max(0, int((a - 0.05) * SR)) : int((b + 0.15) * SR)])
    return out


def align(x, texts) -> list[np.ndarray | None]:
    """Gemini Flash 에게 녹음을 들려 줄마다 대략의 시작·끝을 받고 assign 으로 자른다."""
    prompt = (
        "이 오디오는 아래 대사들을 순서대로 연기한 녹음입니다. 각 대사가 오디오에서 시작·끝나는 시각(초)을 찾아 "
        'JSON 배열 [{"i":번호,"start":초,"end":초}] 로만 답하세요. 들리지 않는 대사는 빼세요.\n'
        + "\n".join(f"{i}. {plain(t)}" for i, t in enumerate(texts))
    )
    body = {
        "contents": [
            {"parts": [{"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(wav_bytes(x)).decode()}}, {"text": prompt}]}
        ],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }
    err = ""
    for model in ALIGN_MODELS:  # 붐비거나(503) 한도가 끝나면 다음 모델로
        try:
            d = _post(model, body)
            break
        except urllib.error.HTTPError as e:
            err = f"{model} {e.code}: {_redact(e.read().decode()[:200])}"
        except (TimeoutError, urllib.error.URLError) as e:
            err = f"{model} {type(e).__name__}"
    else:
        raise VoiceError(f"정렬 실패 {err}")
    marks = {int(m["i"]): (float(m["start"]), float(m["end"])) for m in json.loads(d["candidates"][0]["content"]["parts"][0]["text"])}
    return assign(x, marks, len(texts))


def cps(y, text) -> float:
    """초당 글자 수."""
    return len(speak(text).replace(" ", "")) / max(len(y) / SR, 1e-6)


def ok_len(y, text) -> bool:
    """초당 3~12글자면 정상 (너무 길면 다른 줄이 섞였거나 헛소리)."""
    return len(y) > 0 and 3.0 <= cps(y, text) <= 12


def transcribe(y) -> str | None:
    """녹음을 받아적는다 (무료 텍스트 모델을 차례로). 다 막히면 None."""
    body = {
        "contents": [
            {
                "parts": [
                    {"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(wav_bytes(y)).decode()}},
                    {"text": "이 한국어 오디오를 들리는 그대로 받아적어. 받아적은 글자만 답해."},
                ]
            }
        ],
        "generationConfig": {"temperature": 0},
    }
    for model in ALIGN_MODELS:
        try:
            return _post(model, body)["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (urllib.error.HTTPError, TimeoutError, urllib.error.URLError, KeyError, IndexError):
            continue
    return None


def heard(y, text) -> bool | None:
    """녹음이 대사와 맞는지. 받아적기를 못 하면 None (모름)."""
    got = transcribe(y)
    if got is None:
        return None
    n_got, n_want = len(norm_text(got)), len(norm_text(speak(text)))
    # 지시문을 같이 읽으면 글자가 확 늘어난다 → 길이도 본다
    # 잘려서 끝이 빠져도 글자가 확 준다 → 양쪽 다 본다
    return similar(got, speak(text)) >= 0.7 and n_want * 0.88 <= n_got <= n_want * 1.25 + 2


def norm_text(t: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", t.upper().replace("AI", "에이아이"))


def similar(a: str, b: str) -> float:
    """띄어쓰기·문장부호를 빼고 비교한 글자 일치율."""
    return difflib.SequenceMatcher(None, norm_text(a), norm_text(b)).ratio()


def good(y, ln, log=print) -> bool:
    if y is None or not ok_len(y, ln["text"]):
        return False
    ok = heard(y, ln["text"])
    if ok is False:
        log(f"다른 말이 녹음됨: {plain(ln['text'])}")
    return ok is not False


# ---------- 만들기 ----------
def fake(ep, work, lines) -> None:
    """네트워크 없이 길이만 맞춘 조용한 삐 소리."""
    for ln in lines:
        p = path_of(ep, work, ln, fake=True)
        if p.exists():
            continue
        sec = max(0.8, len(plain(ln["text"]).replace(" ", "")) / FAKE_CPS)
        t = np.arange(int(SR * sec)) / SR
        write_wav(p, np.sin(2 * np.pi * 220 * t) * 0.2)


def make(ep, work, lines, log=print) -> None:
    """없는 줄만 녹음한다. 묶음 원본은 work/voice/raw/ 에 남겨서 다시 돌려도 요청을 아낀다."""
    if all(path_of(ep, work, ln).exists() for ln in lines):
        return
    if not os.environ.get("GEMINI_API_KEY"):
        raise VoiceError("GEMINI_API_KEY 가 없음 (길이만 보려면 --fake-voice)")
    raw = Path(work) / "voice" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for g in groups(lines):
        if all(path_of(ep, work, ln).exists() for ln in g):
            continue
        rawf = raw / f"{hashlib.sha1('|'.join(key_of(ep, ln) for ln in g).encode()).hexdigest()[:12]}.wav"
        if rawf.exists():
            x, _ = read_wav(rawf)
        else:
            try:
                x = request(ep, g, log)
            except VoiceError as e:
                if "모두 끝남" not in str(e):
                    raise
                for ln in g:  # TTS 한도가 다 끝나면 Live 로 한 줄씩
                    if not path_of(ep, work, ln).exists():
                        by_live(ep, work, ln, log)
                continue
            write_wav(rawf, x)
            time.sleep(WAIT)
        parts = align(x, [ln["text"] for ln in g]) if len(g) > 1 else [trim(x)]
        for ln, part in zip(g, parts, strict=True):
            if not path_of(ep, work, ln).exists():
                fix_line(ep, work, ln, part, log)


def retake(ep, ln, log) -> np.ndarray | None:
    """한 줄만 다시 녹음. TTS 한도가 다 끝났으면 None."""
    try:
        y = trim(request(ep, [ln], log))
    except VoiceError as e:
        if "모두 끝남" in str(e):
            return None
        raise
    time.sleep(WAIT)
    if not ok_len(y, ln["text"]):  # 지시문을 읽거나 길게 쉰 녹음이면 대사 부분만 찾아 자른다
        cut = align(y, [ln["text"]])[0]
        y = y if cut is None else cut
    return y


def fix_line(ep, work, ln, y, log) -> None:
    """묶음에서 잘라낸 줄을 확인하고, 틀리면 다시 녹음(TTS → Live 순)해서 저장한다."""
    tries = []
    for _ in range(3):
        if good(y, ln, log):
            break
        log(f"따로 다시 녹음: {plain(ln['text'])}")
        y = retake(ep, ln, log)
        if y is None:
            break
        if heard(y, ln["text"]) is not False:
            tries.append(y)
    else:
        y = min(tries, key=lambda t: abs(cps(t, ln["text"]) - 7)) if tries else None  # 그나마 정상 속도에 가까운 것
        if y is not None and not 1.5 <= cps(y, ln["text"]) <= 16:
            y = None
    if y is None:
        by_live(ep, work, ln, log)
        return
    write_wav(path_of(ep, work, ln), y)
    log(f"목소리 {ln['who']}: {plain(ln['text'])} ({len(y) / SR:.1f}초)")


def by_live(ep, work, ln, log) -> None:
    """Gemini Live 로 한 줄 녹음 (최대 3번, 받아적어 맞는 것만)."""
    from . import live

    for _ in range(3):
        x = live.say(ep["gvoices"][ln["who"]], speak(ln["text"]), ln.get("how", "자연스럽게"))
        if x is None:
            break
        y = trim(x)
        if heard(y, ln["text"]) is not False:
            write_wav(path_of(ep, work, ln), y)
            log(f"목소리 {ln['who']} (Live): {plain(ln['text'])} ({len(y) / SR:.1f}초)")
            return
        log(f"Live 가 다른 말을 함: {plain(ln['text'])}")
    raise VoiceError(f"무료 목소리를 모두 써 봤지만 녹음 실패: {plain(ln['text'])} (내일 다시)")
