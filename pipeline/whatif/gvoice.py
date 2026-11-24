"""감정 연기 목소리: Gemini 무료 TTS (여러 줄을 한 번에 연기시키고, 쉼 위치로 줄마다 자른다).

- 연속된 대사를 화자 2명 이하 묶음으로 보내 장면 흐름째 연기하게 한다 (요청 수 = 편당 5~6번, 무료 한도 안).
- 줄마다 "how" (감정 지시)를 괄호로 넣는다.
- 키는 환경변수 GEMINI_API_KEY 로만 받는다 (저장소·로그에 남기지 않는다).
"""
import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

SR = 24000
MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")


def plain(s):
    return s.replace("*", "")


def key_of(ep, ln):
    v = ep["gvoices"][ln["who"]]
    return hashlib.sha1(f'{v}|{ln["who"]}|{plain(ln["text"])}|{ln.get("how", "")}'.encode()).hexdigest()[:12]


def path_of(ep, work, ln):
    return Path(work) / "voice" / f'g-{ln["who"]}-{key_of(ep, ln)}.wav'


def groups(ep, lines, max_lines=5):
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


def request(ep, grp):
    names = ep.get("names", {})
    label = lambda w: re.sub(r"\s|\(|\)", "", names.get(w, w)) or w   # noqa: E731
    spk = list(dict.fromkeys(ln["who"] for ln in grp))
    cast = ep.get("gcast", {})
    head = ep.get("gdirect", "") + "\n" + "\n".join(f"- {label(w)}: {cast.get(w, '')}" for w in spk)
    body_lines = "\n".join(f'{label(ln["who"])}: ({ln.get("how", "자연스럽게")}) {plain(ln["text"])}' for ln in grp)
    prompt = f"{head}\n대사마다 감정을 크게 살려 연기하고, 대사와 대사 사이는 반드시 2초 동안 완전히 조용히 쉬세요. 괄호 안 지시는 읽지 마세요.\n\n{body_lines}"
    if len(spk) == 1:
        sc = {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": ep["gvoices"][spk[0]]}}}
    else:
        sc = {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": label(w), "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": ep["gvoices"][w]}}} for w in spk]}}
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": sc}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for k in range(4):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=300))
            a = base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
            return np.frombuffer(a, dtype=np.int16).astype(np.float32) / 32768
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code == 429 and "PerDay" in msg:
                raise SystemExit("Gemini 무료 하루 한도 소진")
            if e.code in (429, 500, 503) and k < 3:
                time.sleep(30 * (k + 1))
                continue
            raise SystemExit(f"Gemini TTS 실패 {e.code}: {re.sub(r'AIza[0-9A-Za-z_-]+', '***', msg)}")
        except (KeyError, IndexError):
            if k < 3:
                time.sleep(10)
                continue
            raise


def split(x, texts):
    """쉼(조용한 구간) 후보 중에서, 글자 수 비율에 가장 맞게 len(texts)-1 곳을 골라 자른다."""
    n = len(texts)
    hop = int(SR * .02)
    env = np.array([np.abs(x[i:i + hop]).max() for i in range(0, len(x) - hop, hop)])
    quiet = env < max(.015, env.max() * .03)
    runs, s = [], None
    for i, q in enumerate(quiet):
        if q and s is None:
            s = i
        if not q and s is not None:
            if i - s >= 8:   # 0.16초 이상
                runs.append(((s + i) / 2 * hop, (i - s) * hop))
            s = None
    voiced = np.nonzero(~quiet)[0]
    a, b = voiced[0] * hop, voiced[-1] * hop + hop
    runs = [r for r in runs if a < r[0] < b]
    if n == 1:
        return [x[max(0, a - 2400):b + 4800]]
    if len(runs) < n - 1:
        raise RuntimeError(f"쉼이 부족함: {len(runs)} < {n - 1}")
    w = np.array([len(plain(t).replace(" ", "")) + 2 for t in texts], float)
    target = a + (b - a) * np.cumsum(w)[:-1] / w.sum()
    # DP: 순서대로 n-1개 선택, 비용 = 목표 위치와의 거리 - 쉼 길이 보너스
    R = len(runs)
    INF = 1e18
    cost = np.full((n, R), INF)
    prev = np.zeros((n, R), int)
    for j in range(R):
        cost[1, j] = abs(runs[j][0] - target[0]) / SR - 1.5 * runs[j][1] / SR
    for k in range(2, n):
        for j in range(R):
            best = INF
            for i in range(j):
                if cost[k - 1, i] < best:
                    best, prev[k, j] = cost[k - 1, i], i
            cost[k, j] = best + abs(runs[j][0] - target[k - 1]) / SR - 1.5 * runs[j][1] / SR
    j = int(np.argmin(cost[n - 1]))
    cut = [j]
    for k in range(n - 1, 1, -1):
        j = prev[k, j]
        cut.append(j)
    cut = [int(runs[c][0]) for c in reversed(cut)]
    edges = [a] + cut + [b]
    out = []
    for k in range(n):
        seg = x[edges[k]:edges[k + 1]]
        e = np.array([np.abs(seg[i:i + hop]).max() for i in range(0, max(1, len(seg) - hop), hop)])
        v = np.nonzero(e >= max(.015, e.max() * .03))[0]
        s0, s1 = (v[0] * hop, v[-1] * hop + hop) if len(v) else (0, len(seg))
        out.append(seg[max(0, s0 - 1200):s1 + 3600])
    return out


def wav_bytes(y):
    import io
    import wave
    b = io.BytesIO()
    with wave.open(b, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    return b.getvalue()


def align(x, texts):
    """Gemini(텍스트 모델, TTS와 다른 무료 한도)에게 녹음을 들려 대사마다 대략의 시작·끝을 받고,
    소리 덩어리(0.25초 이상 쉼으로 나눈 구간)를 가장 많이 겹치는 대사에 붙인다. 빠진 대사는 None."""
    prompt = ("이 오디오는 아래 대사들을 순서대로 연기한 녹음입니다. 각 대사가 오디오에서 시작·끝나는 시각(초)을 찾아 "
              'JSON 배열 [{"i":번호,"start":초,"end":초}] 로만 답하세요. 들리지 않는 대사는 빼세요.\n'
              + "\n".join(f"{i}. {plain(t)}" for i, t in enumerate(texts)))
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(wav_bytes(x)).decode()}},
                                    {"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    marks = {int(m["i"]): (float(m["start"]), float(m["end"])) for m in json.loads(d["candidates"][0]["content"]["parts"][0]["text"])}
    hop = int(SR * .02)
    env = np.array([np.abs(x[i:i + hop]).max() for i in range(0, len(x) - hop, hop)])
    loud = env >= max(.015, env.max() * .03)
    segs, s, gap = [], None, 0
    for i, v in enumerate(loud):
        if v:
            if s is None:
                s = i
            gap, e = 0, i
        elif s is not None:
            gap += 1
            if gap >= 13:
                segs.append((s * hop / SR, (e + 1) * hop / SR))
                s = None
    if s is not None:
        segs.append((s * hop / SR, (e + 1) * hop / SR))
    own = {}
    for a, b in segs:
        best, bi = 0, None
        for i, (ms, me) in marks.items():
            ov = min(b, me + .2) - max(a, ms - .2)
            if ov > best:
                best, bi = ov, i
        if bi is not None:
            own.setdefault(bi, []).append((a, b))
    out = []
    for i in range(len(texts)):
        if i not in own:
            out.append(None)
            continue
        a, b = own[i][0][0], own[i][-1][1]
        out.append(x[max(0, int((a - .05) * SR)):int((b + .15) * SR)])
    return out


def ok_len(y, text):
    cps = len(plain(text).replace(" ", "")) / (len(y) / SR)
    return 3.0 <= cps <= 12


def write_wav(path, y):
    import wave
    path.parent.mkdir(parents=True, exist_ok=True)
    y = np.clip(y, -1, 1)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((y * 32767).astype(np.int16).tobytes())


def make(ep, work, lines):
    todo = [ln for ln in lines if not path_of(ep, work, ln).exists()]
    if not todo:
        return
    raw = Path(work) / "voice" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    gs = groups(ep, lines)
    for gi, g in enumerate(gs):
        if all(path_of(ep, work, ln).exists() for ln in g):
            continue
        rawf = raw / f"group{gi}.wav"
        if rawf.exists():
            import wave
            with wave.open(str(rawf)) as f:
                x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
        else:
            x = request(ep, g)
            write_wav(rawf, x)
            time.sleep(21)   # 무료 등급 분당 3회
        parts = align(x, [ln["text"] for ln in g])
        for ln, p in zip(g, parts):
            if p is None or not ok_len(p, ln["text"]):
                for k in range(3):
                    print(f"따로 다시 녹음: {plain(ln['text'])}", flush=True)
                    p = split(request(ep, [ln]), [ln["text"]])[0]
                    time.sleep(21)
                    if ok_len(p, ln["text"]):
                        break
            write_wav(path_of(ep, work, ln), p)
            print(f"목소리 {ln['who']}: {plain(ln['text'])} ({len(p) / SR:.1f}초)", flush=True)
