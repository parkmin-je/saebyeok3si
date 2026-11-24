"""느린 우체통 한 편 만들기: 이야기 파일 하나 → 목소리 → 타임라인 → 장면 렌더 → 음악·생활 소리 → 완성 영상.

python pipeline/saeyeon/build.py pipeline/saeyeon/ep002/episode.json <작업폴더> [--only-audio] [--jobs 4] [--fake-tts]

episode.json
{
 "id", "title", "brand", "voices": {"nar": "Charon", ...}, "names": {"son": "김영수 (72)", ...},
 "intro": {"scene": {"scene": "mailbox", "o": {...}}, "lines": [{"who","tone","text"}]},
 "stories": [{"kicker": "첫 번째 편지", "title": "아버지의 시계",
              "scenes": [{"scene", "o", "label", "memory", "snow", "lines": [...]}], "rest": {"scene", "o"}}],
 "outro": {"scene": {...}, "lines": [...], "question": "...", "s": "..."}
}
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))
from pipeline.episode.score import SR, Track, _t, bass, bell, epiano, hz, pad, reverb  # noqa: E402

GAP_LINE, GAP_SCENE, TITLE, STORY_CARD, REST, END = 0.55, 1.2, 5.0, 4.5, 7.0, 7.0


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip())


def pieces(text, short=46, long=60):
    """긴 낭독 한 덩어리를 자막 두세 줄 크기로 나눈다 (문장 → 너무 길면 쉼표)."""
    out = []
    for sen in re.split(r"(?<=[.?!…])\s+", text.strip()):
        cuts = [m.start() for m in re.finditer(", ", sen) if 8 <= m.start() <= len(sen) - 9]
        if len(sen) > long and cuts:
            cut = min(cuts, key=lambda i: abs(i - len(sen) / 2)) + 1
            parts = [sen[:cut].strip(), sen[cut:].strip()]
        else:
            parts = [sen]
        for x in parts:
            if out and len(out[-1]) + len(x) + 1 <= short:
                out[-1] += " " + x
            else:
                out.append(x)
    return out


def voice_file(work, line, voice):
    say = f"[{line['tone']}] {line['text']}" if line.get("tone") else line["text"]
    return say, work / "voice" / f"{hashlib.md5((say + voice).encode()).hexdigest()[:12]}.wav"


def all_lines(ep):
    if ep.get("short"):
        for sc in ep["scenes"]:
            yield from sc.get("lines", [])
        return
    yield from ep["intro"]["lines"]
    for st in ep["stories"]:
        for sc in st["scenes"]:
            yield from sc["lines"]
    yield from ep["outro"]["lines"]


_ST = {}


def supertonic(text, voice, out, speed=0.92, steps=10):
    """Supertonic 3 (코드 MIT, 모델 OpenRAIL-M): CPU에서 도는 무료 한국어 목소리. voice = M1~M5, F1~F5."""
    import soundfile as sf
    if "tts" not in _ST:
        from supertonic import TTS
        _ST["tts"] = TTS(auto_download=True)
    tts = _ST["tts"]
    style = _ST.setdefault(voice, tts.get_voice_style(voice_name=voice))
    wav, _ = tts.synthesize(text, voice_style=style, lang="ko", speed=speed, total_steps=steps, silence_duration=0.35)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), np.asarray(wav).reshape(-1), tts.sample_rate)


def make_voices(ep, work, fake):
    from pipeline.episode.edit import tts
    todo = [(ln, *voice_file(work, ln, ep["voices"][ln["who"]])) for ln in all_lines(ep)]
    for i, (ln, say, out) in enumerate(todo):
        if not out.exists():
            v = ep["voices"][ln["who"]]
            if re.fullmatch(r"[MF][1-5]", v) and not fake:
                supertonic(ln["text"], v, out, ep.get("speed", {}).get(ln["who"], 0.92))
            else:
                tts(say, v, out, fake)
            print(f"목소리 {i + 1}/{len(todo)}", out.name, flush=True)


def timeline(ep, work):
    segs, lines, cards, cues = [], [], [], []
    t = 0.0
    cards.append({"start": 0, "end": TITLE, "kicker": ep.get("brand", ""), "main": ep["title"].replace("|", "<br>")})
    t = TITLE - 0.6

    def scene(sc, kind):
        nonlocal t
        start = t
        for k, ln in enumerate(sc.get("lines", [])):
            _, f = voice_file(work, ln, ep["voices"][ln["who"]])
            t += (0.9 if k == 0 else GAP_LINE)
            d = dur(f)
            ps = pieces(ln["text"], 30, 38) if ep.get("short") else pieces(ln["text"])
            w = [len(x.replace(" ", "")) + 2 for x in ps]
            u = t
            for j, (x, wj) in enumerate(zip(ps, w)):
                e = u + d * wj / sum(w)
                lines.append({"who": ln["who"], "name": ep.get("names", {}).get(ln["who"], ""), "text": x,
                              "start": round(u, 3), "end": round(e - (.12 if j < len(ps) - 1 else 0), 3),
                              **({"wav": str(f)} if j == 0 else {})})
                u = e
            t += d
        t += sc.get("hold", 0.8 if sc.get("lines") else REST)
        segs.append({"scene": sc["scene"], "o": sc.get("o", {}), "start": round(max(0, start), 3), "end": round(t, 3), "fx": sc.get("fx", .5), "stage": sc.get("stage"),
                     "label": sc.get("label"), "memory": sc.get("memory", False), "snow": sc.get("snow", False),
                     "zoom": sc.get("zoom", .07), "pan": sc.get("pan", 0)})
        cues.append({"t": start, "mood": "memory" if sc.get("memory") else kind, "scene": sc["scene"]})
        t += GAP_SCENE * 0

    if ep.get("short"):   # 세로 쇼츠: 제목 카드 없이 바로 장면 + 첫 줄 훅, 끝에 짧은 질문 카드
        cards.clear()
        t = -0.6
        for sc in ep["scenes"]:
            scene(sc, "warm")
        cards.append({"start": round(t, 3), "end": round(t + 3.5, 3), "kicker": ep.get("brand", ""),
                      "main": ep["end"]["question"].replace("|", "<br>"), "s": ep["end"].get("s", "")})
        t += 3.5
        tl = {"brand": ep.get("brand", ""), "title": ep["title"].replace("|", "<br>"), "vertical": True,
              "segments": segs, "lines": lines, "cards": cards, "cues": cues, "total": round(t, 3)}
        (work / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
        return tl
    intro = dict(ep["intro"]["scene"], lines=ep["intro"]["lines"], label=ep["intro"].get("label"))
    scene(intro, "warm")
    for st in ep["stories"]:
        cards.append({"start": round(t, 3), "end": round(t + STORY_CARD, 3), "kicker": st["kicker"], "main": st["title"]})
        cues.append({"t": t, "mood": "card", "scene": "card"})
        t += STORY_CARD - 0.4
        for sc in st["scenes"]:
            scene(sc, "warm")
        if st.get("rest"):
            scene(dict(st["rest"], lines=[]), "rest")
    out = dict(ep["outro"]["scene"], lines=ep["outro"]["lines"], label=ep["outro"].get("label"))
    scene(out, "warm")
    cards.append({"start": round(t, 3), "end": round(t + END, 3), "kicker": ep.get("brand", ""),
                  "main": ep["outro"]["question"].replace("|", "<br>"), "s": ep["outro"].get("s", "")})
    t += END
    tl = {"brand": ep.get("brand", ""), "segments": segs, "lines": lines, "cards": cards, "cues": cues, "total": round(t, 3)}
    (work / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    return tl


# ---------- 소리 ----------
def rd(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def music(total, seed=0):
    """따뜻한 장조 피아노·패드 (70bpm, C-Am-F-G / F-G-Em-Am 번갈아)."""
    rng = np.random.default_rng(seed)
    tr = Track(total + 2)
    beat = 60 / 70
    bar = 4 * beat
    progs = [[("C3", ["E4", "G4", "C5"]), ("A2", ["E4", "A4", "C5"]), ("F2", ["F4", "A4", "C5"]), ("G2", ["D4", "G4", "B4"])],
             [("F2", ["F4", "A4", "C5"]), ("G2", ["D4", "G4", "B4"]), ("E2", ["E4", "G4", "B4"]), ("A2", ["E4", "A4", "C5"])]]
    mels = [["E5", None, "G5", None], ["C5", None, "E5", None], ["A4", None, "C5", "F5"], ["D5", None, "B4", None],
            ["A4", "C5", None, None], ["B4", None, "D5", None], ["G4", None, "B4", None], ["C5", None, "E5", "A5"]]
    m = 0
    while m * bar < total:
        t0 = m * bar
        prog = progs[(m // 8) % 2]
        root, ch = prog[m % 4]
        tr.add(pad([hz(c) for c in ch], bar + .6, .35), t0)
        tr.add(bass(hz(root), bar * .95, .32), t0)
        for k in (0, 2):
            for c in ch:
                tr.add(epiano(hz(c), beat * 1.6, .11), t0 + k * beat + rng.normal(0, .008))
        if m % 8 >= 2:
            for k, n in enumerate(mels[(m + (m // 8)) % 8 if m % 2 else m % 4]):
                if n:
                    tr.add(bell(hz(n), beat, .09), t0 + k * beat)
        m += 1
    x = reverb(tr.x, 2.2, .35)[:int(total * SR)]
    return x / (np.abs(x).max() + 1e-9)


def noise(n, rng, smooth):
    x = rng.standard_normal(n)
    return np.convolve(x, np.ones(smooth) / smooth, "same") if smooth > 1 else x


def ambience(scene, n, t0, rng):
    """장면별 생활 소리 (작게)."""
    t = np.arange(n) / SR
    if scene in ("watch", "gears"):
        out = np.zeros(n)
        tk = _t(.03)
        for k in np.arange(0, n / SR, .5):
            c = noise(len(tk), rng, 1) * np.exp(-tk * 300)
            c = c - np.convolve(c, np.ones(3) / 3, "same")
            i = int(k * SR)
            out[i:i + len(c)] += c[:n - i] * (.16 if int(k * 2) % 2 == 0 else .1)
        return out
    if scene == "sea":
        w = noise(n, rng, 40)
        return w / (np.abs(w).max() + 1e-9) * (.5 + .5 * np.sin(2 * np.pi * t / 6.5) ** 2) * .22
    if scene == "station":
        r = noise(n, rng, 200)
        r = r / (np.abs(r).max() + 1e-9)
        clack = np.zeros(n)
        for k in np.arange(0, n / SR, .42):
            i = int(k * SR)
            c = noise(int(.05 * SR), rng, 4) * np.exp(-_t(.05) * 80)
            clack[i:i + len(c)] += c[:n - i] * .25
        env = np.clip(1 - np.abs(t / (n / SR) - .5) * 1.6, .15, 1)
        return (r * .2 + clack) * env
    if scene == "kitchen":
        out = noise(n, rng, 8) * .03
        for k in rng.uniform(0, n / SR, int(n / SR * 3)):
            i = int(k * SR)
            c = noise(int(.02 * SR), rng, 1) * np.exp(-_t(.02) * 200)
            out[i:i + len(c)] += c[:n - i] * .2
        return out
    if scene == "snowroad":
        w = noise(n, rng, 120)
        return w / (np.abs(w).max() + 1e-9) * (.6 + .4 * np.sin(2 * np.pi * t / 9)) * .12
    if scene in ("alley", "busstop", "countryhouse", "dabang", "classroom", "mailbox", "sunrise"):
        w = noise(n, rng, 60)
        return w / (np.abs(w).max() + 1e-9) * .04
    return np.zeros(n)


def mix(tl, work):
    total = tl["total"]
    N = int(total * SR)
    voice = np.zeros(N)
    for ln in tl["lines"]:
        if "wav" not in ln:
            continue
        v = rd(ln["wav"])
        v = v / (np.abs(v).max() + 1e-9) * .85
        i = int(ln["start"] * SR)
        voice[i:i + len(v)] += v[:max(0, N - i)]
    mus = music(total)
    tt = np.arange(N) / SR
    env = np.full(N, .22)
    for s in tl["segments"]:
        if s["memory"]:
            env[(tt > s["start"]) & (tt < s["end"])] = .14
        if s["scene"] in ("sunrise", "sea") and not any(ln["start"] < s["end"] and ln["end"] > s["start"] for ln in tl["lines"]):
            env[(tt > s["start"]) & (tt < s["end"])] = .34   # 쉬는 장면은 음악을 올린다
    for c in tl["cards"]:
        env[(tt > c["start"]) & (tt < c["end"])] = .32
    env = np.convolve(env, np.ones(SR) / SR, "same")
    speak = (np.abs(voice) > .02).astype(float)
    duck = np.convolve(speak, np.ones(int(SR * .4)) / (SR * .4), "same")
    mus = mus * env * (1 - .45 * np.clip(duck * 3, 0, 1))
    amb = np.zeros(N)
    rng = np.random.default_rng(9)
    for s in tl["segments"]:
        a, b = int(max(0, s["start"] - .5) * SR), int(min(total, s["end"] + .5) * SR)
        x = ambience(s["scene"], b - a, s["start"], rng)
        f = min(len(x) // 2, SR)
        if f:
            x[:f] *= np.linspace(0, 1, f)
            x[-f:] *= np.linspace(1, 0, f)
        amb[a:b] += x * (.6 if s["memory"] else 1)
    out = voice + mus + amb
    fade = int(SR * 2.5)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.abs(out).max() + 1e-9) * .9
    out.astype(np.float32).tofile(work / "mix.f32")


def render(tl, work, jobs):
    """구간을 나눠 Playwright 여러 개로 동시에 프레임을 찍는다."""
    total = tl["total"]
    frames = work / "frames"
    frames.mkdir(exist_ok=True)
    cuts = np.linspace(0, total, jobs + 1)

    def run(k):
        subprocess.run(["node", str(HERE / "render2.js"), str(work / "timeline.json"), str(frames), "full",
                        f"{cuts[k]:.3f}", f"{cuts[k + 1]:.3f}"], check=True)
    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(run, range(jobs)))


def encode(tl, work, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(work / "frames" / "%06d.jpg"),
                    "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(work / "mix.f32"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)],
                   check=True)


def chapters(ep, tl):
    """유튜브 설명란용 챕터 (이야기마다)."""
    if ep.get("short"):
        return ep["title"].replace("|", " ")
    rows = ["00:00 " + ep["title"].replace("|", " ")]
    for c in tl["cards"][1:-1]:
        s = int(c["start"])
        rows.append(f"{s // 60:02d}:{s % 60:02d} {c['kicker']} · {c['main']}")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("work")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4)))
    ap.add_argument("--fake-tts", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--voices-only", action="store_true")
    a = ap.parse_args()
    ep = json.loads(Path(a.episode).read_text())
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    make_voices(ep, work, a.fake_tts)
    if a.voices_only:
        return
    tl = timeline(ep, work)
    print(f"길이 {tl['total'] / 60:.1f}분, 장면 {len(tl['segments'])}개, 대사 {len(tl['lines'])}줄", flush=True)
    (work / "chapters.txt").write_text(chapters(ep, tl))
    mix(tl, work)
    if a.no_render:
        return
    render(tl, work, a.jobs)
    encode(tl, work, work / f"{ep['id']}.mp4")
    print("완성", work / f"{ep['id']}.mp4")


if __name__ == "__main__":
    main()
