"""만약에 쇼츠 만들기: 대본(shots) → 목소리 → 컷 타임라인·자막 덩어리 → 신나는 음악+효과음 → 세로 렌더 → mp4.

python pipeline/whatif/make.py pipeline/whatif/w01-dog.json <작업폴더> [--jobs 4] [--fake-tts] [--voices-only]
대본: {"id","brand","hook","voices","speed","names","shots":[{"scene"|"img","o","cam","cam2","kb","stage","say":{"who","text"},"hold","shake"}],"card":{"q","s"}}
자막 강조는 *단어* 로 표시 (목소리에는 별표를 뺀다).
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from pipeline.episode.score import SR, Track, _t, bass, bell, epiano, hz, pad, reverb  # noqa: E402
from pipeline.saeyeon.build import dur, rd, supertonic, voice_file  # noqa: E402

GAP, HOLD, CARD = 0.12, 1.4, 3.2


def plain(s):
    return s.replace("*", "")


def lines(ep):
    return [s["say"] for s in ep["shots"] if s.get("say")]


def make_voices(ep, work, fake):
    if ep.get("gvoices") and not fake:
        from pipeline.whatif import gvoice
        gvoice.make(ep, work, lines(ep))
        return
    from pipeline.episode.edit import tts
    for ln in lines(ep):
        v = ep["voices"][ln["who"]]
        _, out = voice_file(work, {"text": plain(ln["text"])}, v + str(ep.get("speed", {}).get(ln["who"], 1.0)))
        if out.exists():
            continue
        if fake:
            tts(plain(ln["text"]), v, out, True)
        else:
            supertonic(plain(ln["text"]), v, out, ep.get("speed", {}).get(ln["who"], 1.0))
        print("목소리", out.name, flush=True)


def chunks(text, n=11):
    """자막을 2~4어절 덩어리로 (화면에 한 줄~두 줄)."""
    out, cur = [], ""
    for w in text.split():
        if cur and len(plain(cur + " " + w)) > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
        if re.search(r"[.?!]$", plain(w)) and len(plain(cur)) >= 5:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    fixed, open_ = [], False   # *강조* 가 두 덩어리에 걸치면 양쪽을 각각 닫고 연다
    for c in out:
        c2 = ("*" if open_ else "") + c
        if c2.count("*") % 2:
            c2 += "*"
            open_ = not open_ if c.count("*") % 2 else open_
        fixed.append(c2.replace("**", ""))
    return fixed


def vpath(ep, work, ln):
    """목소리 파일. ep["fx"][who] = 음높이 배수 (예: 1.25) 면 높고 작은 목소리(강아지)로 바꾼 사본을 쓴다."""
    if ep.get("gvoices") and not ep.get("_fake"):
        from pipeline.whatif import gvoice
        f = gvoice.path_of(ep, work, ln)
    else:
        _, f = voice_file(work, {"text": plain(ln["text"])}, ep["voices"][ln["who"]] + str(ep.get("speed", {}).get(ln["who"], 1.0)))
    k = ep.get("fx", {}).get(ln["who"])
    if not k:
        return f
    g = f.with_name(f.stem + f"-fx{k}.wav")
    if not g.exists():
        sr = int(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout.strip())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-af",
                        f"asetrate={int(sr * k)},aresample={sr},atempo={1 / k * ep.get('fxtempo', {}).get(ln['who'], 1.08):.4f},"
                        "equalizer=f=3000:t=q:w=1:g=3,volume=1.1", str(g)], check=True)
    return g


def timeline(ep, work):
    shots, caps, cuts, stages = [], [], [], []
    t = 0.0
    for s in ep["shots"]:
        start = t
        if s.get("say"):
            ln = s["say"]
            f = vpath(ep, work, ln)
            d = dur(f)
            cs = chunks(ln["text"])
            w = [len(plain(c).replace(" ", "")) + 1.5 for c in cs]
            u = t + .05
            for k, c in enumerate(cs):
                e = u + (d - .1) * w[k] / sum(w)
                caps.append({"who": ln["who"], "name": ep.get("names", {}).get(ln["who"], ""), "text": c,
                             "start": round(u, 3), "end": round(e, 3), **({"wav": str(f)} if k == 0 else {})})
                u = e
            t += d + GAP + s.get("after", 0)
        else:
            t += s.get("hold", HOLD)
        sh = {k: v for k, v in s.items() if k not in ("say", "hold", "after")}
        sh.update(start=round(start, 3), end=round(t, 3))
        shots.append(sh)
        cuts.append(start)
        if s.get("stage"):
            stages.append(start)
    shots[-1]["end"] = round(t + CARD, 3)   # 끝 질문 카드 뒤에도 마지막 장면이 보이게
    card = {"start": round(t, 3), "end": round(t + CARD, 3), "q": ep["card"]["q"], "s": ep["card"].get("s", "")}
    t += CARD
    tl = {"brand": ep.get("brand", ""), "hook": ep.get("hook", ""), "hookEnd": ep.get("hookEnd", 2.6), "shots": shots, "caps": caps,
          "card": card, "total": round(t, 3), "vertical": True, "mood": ep.get("mood", ""), "cuts": cuts, "stages": stages,
          "soft_from": next((s["start"] for s in shots if s.get("soft")), t)}
    (work / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    return tl


# ---------- 소리 ----------
def kick(n_s=.35):
    tt = _t(n_s)
    f = 50 + 90 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)


def clap(rng, n_s=.18):
    tt = _t(n_s)
    x = rng.standard_normal(len(tt)) * np.exp(-tt * 28)
    return x - np.convolve(x, np.ones(6) / 6, "same")


def whoosh(rng, n_s=.32):
    tt = _t(n_s)
    x = rng.standard_normal(len(tt))
    k = np.ones(18) / 18
    x = np.convolve(x, k, "same") - np.convolve(x, np.ones(90) / 90, "same")
    return x * np.sin(np.pi * tt / n_s) ** 2


def music(total, soft_from, seed=1):
    """밝은 장조 (112bpm, C-G-Am-F). soft_from 이후는 드럼 빼고 피아노·패드만 (감동 구간)."""
    rng = np.random.default_rng(seed)
    tr = Track(total + 2)
    beat = 60 / 112
    bar = 4 * beat
    prog = [("C3", ["C4", "E4", "G4"]), ("G2", ["B3", "D4", "G4"]), ("A2", ["C4", "E4", "A4"]), ("F2", ["A3", "C4", "F4"])]
    mel = [["E5", "G5", None, "E5", "D5", None, "C5", None], ["D5", None, "B4", "D5", "G5", None, None, None],
           ["C5", "E5", None, "A5", "G5", None, "E5", None], ["F5", None, "E5", "C5", "D5", None, None, None]]
    m = 0
    while m * bar < total:
        t0 = m * bar
        root, ch = prog[m % 4]
        soft = t0 >= soft_from
        tr.add(pad([hz(c) for c in ch], bar + .4, .3 if soft else .18), t0)
        tr.add(bass(hz(root), bar * .9 if soft else beat * .8, .3), t0)
        for k in range(8):
            tt = t0 + k * beat / 2
            if not soft:
                for c in ch:
                    tr.add(epiano(hz(c) * 2, beat * .35, .05), tt)
                if k % 4 == 0:
                    tr.add(kick() * .55, tt)
                if k % 4 == 2:
                    tr.add(clap(rng) * .16, tt)
                if k % 2 == 1:
                    tr.add(whoosh(rng, .05) * .05, tt)
            n = mel[m % 4][k]
            if n and m >= 1:
                tr.add(bell(hz(n), beat * (1.4 if soft else .9), .07 if soft else .06), tt)
        if not soft and m % 4 != 0:
            tr.add(bass(hz(root), beat * .8, .25), t0 + 2 * beat)
        m += 1
    x = reverb(tr.x, 1.4, .25)[:int(total * SR)]
    return x / (np.abs(x).max() + 1e-9)


def music_mystery(total, soft_from, seed=1):
    """살금살금 미스터리 (A단조 96bpm): 짧게 튕기는 피아노 + 째깍 하이햇 + 스타카토 베이스. soft_from 이후 = 낮은 드론 + 심장박동."""
    rng = np.random.default_rng(seed)
    tr = Track(total + 2)
    beat = 60 / 96
    bar = 4 * beat
    prog = [("A2", ["A3", "C4", "E4"]), ("F2", ["A3", "C4", "F4"]), ("D2", ["A3", "D4", "F4"]), ("E2", ["G#3", "B3", "E4"])]
    walk = [["A2", None, "E2", None, "A2", "C3", None, "E3"], ["F2", None, "C3", None, "F2", "A2", None, "C3"],
            ["D2", None, "A2", None, "D2", "F2", None, "A2"], ["E2", None, "B2", None, "E2", "G#2", None, "B2"]]
    mel = [["E5", None, "C5", None, "A4", None, None, "B4"], ["C5", None, "A4", None, "F4", None, None, None],
           ["D5", None, "F5", None, "A5", None, "G#5", None], ["E5", None, None, None, "B4", None, "G#4", None]]
    m = 0
    while m * bar < total:
        t0 = m * bar
        root, ch = prog[m % 4]
        soft = t0 >= soft_from
        tr.add(pad([hz(c) for c in ch], bar + .4, .22 if soft else .12), t0)
        if soft:
            tr.add(bass(hz(root) / 2, bar, .35), t0)
            for k in (0, 2):
                tr.add(kick(.3) * .5, t0 + k * beat)
                tr.add(kick(.25) * .3, t0 + k * beat + .22)
        for k in range(8):
            tt = t0 + k * beat / 2
            if not soft:
                n = walk[m % 4][k]
                if n:
                    tr.add(bass(hz(n), beat * .3, .4), tt)
                tr.add(clap(rng, .03) * .05, tt)
                if m >= 1 and mel[m % 4][k]:
                    tr.add(epiano(hz(mel[m % 4][k]), beat * .3, .09), tt)
            elif mel[m % 4][k] and k % 4 == 0:
                tr.add(bell(hz(mel[m % 4][k]), beat * 2, .05), tt)
        m += 1
    x = reverb(tr.x, 1.8, .3)[:int(total * SR)]
    return x / (np.abs(x).max() + 1e-9)


def boom(n_s=1.6):
    tt = _t(n_s)
    f = 38 + 60 * np.exp(-tt * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2)


# ---------- 효과음 (shot["sfx"] = [[이름, 컷 시작부터 초, (길이)]]) ----------
def band(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def tone(f, n_s, decay=8, harm=(1, .3)):
    tt = _t(n_s)
    return sum(a * np.sin(2 * np.pi * f * (k + 1) * tt) for k, a in enumerate(harm)) * np.exp(-tt * decay)


def sfx_make(name, d, rng):
    if name == "ding":
        a, b = tone(hz("E6"), 1.2, 3, (1, .2, .1)), tone(hz("C6"), 1.4, 2.5, (1, .2, .1))
        y = np.zeros(int(SR * 1.8)); y[:len(a)] += a; y[int(SR * .32):int(SR * .32) + len(b)] += b
        return y * .5
    if name == "code":
        y = np.zeros(int(SR * 1.0))
        for k in range(4):
            b = tone(1480, .07, 30, (1,)); i = int(SR * k * .2); y[i:i + len(b)] += b
        return y * .35
    if name == "unlock":
        y = np.zeros(int(SR * .9))
        for k, n in enumerate(["C6", "E6", "G6", "C7"]):
            b = tone(hz(n), .35, 9, (1, .15)); i = int(SR * k * .08); y[i:i + len(b)] += b
        return y * .35
    if name == "steps":
        y = np.zeros(int(SR * (d or 1.0)))
        for k in range(int((d or 1.0) / .16)):
            c = band(rng.standard_normal(int(SR * .05)), 200, 2500) * np.exp(-_t(.05) * 80)
            i = int(SR * (k * .16 + rng.uniform(0, .02))); y[i:i + len(c)] += c * (.8 if k % 2 else 1)
        return y * .5
    if name == "sip":
        n = rng.standard_normal(int(SR * .5))
        f = np.linspace(500, 1400, len(n))
        y = band(n, 300, 3000) * np.sin(np.pi * _t(.5) / .5) ** 2
        return y * (0.5 + .5 * np.sin(2 * np.pi * np.cumsum(f / 200) / SR)) * .25
    if name == "murmur":
        n_s = d or 3
        y = np.zeros(int(SR * n_s))
        for v in range(8):   # 여러 마리가 작게 웅성웅성
            am = np.clip(np.sin(2 * np.pi * rng.uniform(3, 6) * _t(n_s) + rng.uniform(0, 6)), 0, 1) ** 2
            y += band(rng.standard_normal(len(y)), rng.uniform(300, 600), rng.uniform(1200, 2400)) * am
        env = np.minimum(1, np.minimum(_t(n_s) / .5, (n_s - _t(n_s)) / .5))
        return y / (np.abs(y).max() + 1e-9) * env * .18
    if name == "riser":
        n_s = d or 1.5
        tt = _t(n_s)
        y = band(rng.standard_normal(len(tt)), 800, 8000) * (tt / n_s) ** 2 * .5
        y += np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt / n_s) ** 2) / SR) * (tt / n_s) ** 2 * .3
        return y * .5
    if name == "hit":
        w = boom(1.8)
        n = band(rng.standard_normal(len(w)), 60, 3000) * np.exp(-_t(1.8) * 9)
        return (w * .9 + n * .4)
    if name == "heart":
        y = np.zeros(int(SR * .8))
        for o_, a in ((0, 1), (.22, .7)):
            k = kick(.25); i = int(SR * o_); y[i:i + len(k)] += k * a
        return y * .7
    if name == "gasp":
        y = np.zeros(int(SR * .7))
        for v in range(10):
            g = band(rng.standard_normal(int(SR * .45)), rng.uniform(700, 1000), rng.uniform(2200, 3200)) * np.sin(np.pi * _t(.45) / .45) ** 3
            i = int(SR * rng.uniform(0, .2)); y[i:i + len(g)] += g
        return y / (np.abs(y).max() + 1e-9) * .35
    raise ValueError(name)


def mix(tl, work):
    total = tl["total"]
    N = int(total * SR)
    voice = np.zeros(N)
    for c in tl["caps"]:
        if "wav" in c:
            v = rd(c["wav"])
            v = v / (np.abs(v).max() + 1e-9) * .9
            i = int(c["start"] * SR)
            voice[i:i + len(v)] += v[:max(0, N - i)]
    mus = (music_mystery if tl.get("mood") == "mystery" else music)(total, tl["soft_from"])
    speak = (np.abs(voice) > .02).astype(float)
    duck = np.convolve(speak, np.ones(int(SR * .3)) / (SR * .3), "same")
    mus = mus * .32 * (1 - .55 * np.clip(duck * 3, 0, 1))
    sfx = np.zeros(N)
    rng = np.random.default_rng(3)
    for c in tl["cuts"][1:]:
        w = whoosh(rng)
        i = max(0, int((c - .16) * SR))
        sfx[i:i + len(w)] += w[:N - i] * .22
    for s in tl["stages"]:
        b1, b2 = bell(hz("G5"), .6, .3), bell(hz("C6"), .6, .25)
        b = b1[:min(len(b1), len(b2))] + b2[:min(len(b1), len(b2))]
        i = int(s * SR)
        sfx[i:i + len(b)] += b[:N - i] * .5
        if tl.get("mood") == "mystery":
            w = boom()
            sfx[i:i + len(w)] += w[:N - i] * .7
    for sh in tl["shots"]:
        for ev in sh.get("sfx", []):
            y = sfx_make(ev[0], ev[2] if len(ev) > 2 else None, rng)
            i = max(0, int((sh["start"] + ev[1]) * SR))
            if i < N:
                sfx[i:i + len(y)] += y[:N - i]
    i = int(tl["card"]["start"] * SR)
    b = bell(hz("E5"), .5, .3)
    sfx[i:i + len(b)] += b[:N - i] * .4
    out = voice + mus + sfx
    fade = int(SR * 1.2)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.abs(out).max() + 1e-9) * .92
    out.astype(np.float32).tofile(work / "mix.f32")


def render(tl, work, jobs):
    frames = work / "frames"
    frames.mkdir(exist_ok=True)
    cuts = np.linspace(0, tl["total"], jobs + 1)
    env = {**__import__("os").environ, "ENGINE": str(HERE / "punch.html")}

    def run(k):
        subprocess.run(["node", str(HERE.parent / "saeyeon" / "render2.js"), str(work / "timeline.json"), str(frames), "full",
                        f"{cuts[k]:.3f}", f"{cuts[k + 1]:.3f}"], check=True, env=env)
    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(run, range(jobs)))


def encode(work, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(work / "frames" / "%06d.jpg"),
                    "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(work / "mix.f32"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("work")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--fake-tts", action="store_true")
    ap.add_argument("--voices-only", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    ep = json.loads(Path(a.episode).read_text())
    ep["_fake"] = a.fake_tts
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    make_voices(ep, work, a.fake_tts)
    if a.voices_only:
        return
    tl = timeline(ep, work)
    print(f"길이 {tl['total']:.1f}초, 컷 {len(tl['shots'])}개", flush=True)
    mix(tl, work)
    if a.no_render:
        return
    render(tl, work, a.jobs)
    encode(work, work / f"{ep['id']}.mp4")
    print("완성", work / f"{ep['id']}.mp4")


if __name__ == "__main__":
    main()
