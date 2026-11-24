"""배경음악과 효과음. mood: "bright"(기본, 회사 콩트) / "mystery"(섬뜩한 편)."""

import numpy as np

from .synth import SR, band, bass, bell, boom, clap, epiano, hz, kick, pad, put, reverb, t_, tone, whoosh


def bright(total, soft_from, seed=1):
    """밝은 장조 (112bpm, C-G-Am-F). soft_from 이후는 드럼 없이 피아노·패드만."""
    rng = np.random.default_rng(seed)
    buf = np.zeros(int(SR * (total + 4)))
    beat = 60 / 112
    bar = 4 * beat
    prog = [("C3", ["C4", "E4", "G4"]), ("G2", ["B3", "D4", "G4"]), ("A2", ["C4", "E4", "A4"]), ("F2", ["A3", "C4", "F4"])]
    mel = [
        ["E5", "G5", None, "E5", "D5", None, "C5", None],
        ["D5", None, "B4", "D5", "G5", None, None, None],
        ["C5", "E5", None, "A5", "G5", None, "E5", None],
        ["F5", None, "E5", "C5", "D5", None, None, None],
    ]
    m = 0
    while m * bar < total:
        t0 = m * bar
        root, ch = prog[m % 4]
        soft = t0 >= soft_from
        put(buf, pad([hz(c) for c in ch], bar + 0.4, 0.3 if soft else 0.18), t0)
        put(buf, bass(hz(root), bar * 0.9 if soft else beat * 0.8, 0.3), t0)
        for k in range(8):
            tt = t0 + k * beat / 2
            if not soft:
                for c in ch:
                    put(buf, epiano(hz(c) * 2, beat * 0.35, 0.05), tt)
                if k % 4 == 0:
                    put(buf, kick(), tt, 0.55)
                if k % 4 == 2:
                    put(buf, clap(rng), tt, 0.16)
                if k % 2 == 1:
                    put(buf, whoosh(rng, 0.05), tt, 0.05)
            n = mel[m % 4][k]
            if n and m >= 1:
                put(buf, bell(hz(n), beat * (1.4 if soft else 0.9), 0.07 if soft else 0.06), tt)
        if not soft and m % 4 != 0:
            put(buf, bass(hz(root), beat * 0.8, 0.25), t0 + 2 * beat)
        m += 1
    x = reverb(buf, 1.4, 0.25)[: int(total * SR)]
    return x / (np.abs(x).max() + 1e-9)


def mystery(total, soft_from, seed=1):
    """살금살금 (A단조 96bpm). soft_from 이후 = 낮은 드론 + 심장박동."""
    rng = np.random.default_rng(seed)
    buf = np.zeros(int(SR * (total + 4)))
    beat = 60 / 96
    bar = 4 * beat
    prog = [("A2", ["A3", "C4", "E4"]), ("F2", ["A3", "C4", "F4"]), ("D2", ["A3", "D4", "F4"]), ("E2", ["G#3", "B3", "E4"])]
    walk = [
        ["A2", None, "E2", None, "A2", "C3", None, "E3"],
        ["F2", None, "C3", None, "F2", "A2", None, "C3"],
        ["D2", None, "A2", None, "D2", "F2", None, "A2"],
        ["E2", None, "B2", None, "E2", "G#2", None, "B2"],
    ]
    mel = [
        ["E5", None, "C5", None, "A4", None, None, "B4"],
        ["C5", None, "A4", None, "F4", None, None, None],
        ["D5", None, "F5", None, "A5", None, "G#5", None],
        ["E5", None, None, None, "B4", None, "G#4", None],
    ]
    m = 0
    while m * bar < total:
        t0 = m * bar
        root, ch = prog[m % 4]
        soft = t0 >= soft_from
        put(buf, pad([hz(c) for c in ch], bar + 0.4, 0.22 if soft else 0.12), t0)
        if soft:
            put(buf, bass(hz(root) / 2, bar, 0.35), t0)
            for k in (0, 2):
                put(buf, kick(0.3), t0 + k * beat, 0.5)
                put(buf, kick(0.25), t0 + k * beat + 0.22, 0.3)
        for k in range(8):
            tt = t0 + k * beat / 2
            n = mel[m % 4][k]
            if not soft:
                w = walk[m % 4][k]
                if w:
                    put(buf, bass(hz(w), beat * 0.3, 0.4), tt)
                put(buf, clap(rng, 0.03), tt, 0.05)
                if m >= 1 and n:
                    put(buf, epiano(hz(n), beat * 0.3, 0.09), tt)
            elif n and k % 4 == 0:
                put(buf, bell(hz(n), beat * 2, 0.05), tt)
        m += 1
    x = reverb(buf, 1.8, 0.3)[: int(total * SR)]
    return x / (np.abs(x).max() + 1e-9)


MOODS = {"bright": bright, "mystery": mystery}


def _silence(sec):
    return np.zeros(int(SR * sec))


def sfx(name: str, d: float | None, rng) -> np.ndarray:
    """효과음 한 개. 대본에서 shot["sfx"] = [[이름, 컷 시작부터 초, (길이)]] 로 부른다."""
    if name == "ding":
        y = _silence(1.8)
        put(y, tone(hz("E6"), 1.2, 3, (1, 0.2, 0.1)), 0)
        put(y, tone(hz("C6"), 1.4, 2.5, (1, 0.2, 0.1)), 0.32)
        return y * 0.5
    if name == "code":  # 키보드 타닥타닥
        y = _silence(1.0)
        for k in range(4):
            put(y, tone(1480, 0.07, 30, (1,)), k * 0.2)
        return y * 0.35
    if name == "unlock":
        y = _silence(0.9)
        for k, n in enumerate(["C6", "E6", "G6", "C7"]):
            put(y, tone(hz(n), 0.35, 9, (1, 0.15)), k * 0.08)
        return y * 0.35
    if name == "steps":
        sec = d or 1.0
        y = _silence(sec)
        for k in range(int(sec / 0.16)):
            c = band(rng.standard_normal(int(SR * 0.05)), 200, 2500) * np.exp(-t_(0.05) * 80)
            put(y, c, k * 0.16 + rng.uniform(0, 0.02), 0.8 if k % 2 else 1)
        return y * 0.5
    if name == "sip":
        n = rng.standard_normal(int(SR * 0.5))
        f = np.linspace(500, 1400, len(n))
        y = band(n, 300, 3000) * np.sin(np.pi * t_(0.5) / 0.5) ** 2
        return y * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f / 200) / SR)) * 0.25
    if name == "murmur":  # 여럿이 작게 웅성웅성
        sec = d or 3
        y = _silence(sec)
        for _ in range(8):
            am = np.clip(np.sin(2 * np.pi * rng.uniform(3, 6) * t_(sec) + rng.uniform(0, 6)), 0, 1) ** 2
            y += band(rng.standard_normal(len(y)), rng.uniform(300, 600), rng.uniform(1200, 2400)) * am
        env = np.minimum(1, np.minimum(t_(sec) / 0.5, (sec - t_(sec)) / 0.5))
        return y / (np.abs(y).max() + 1e-9) * env * 0.18
    if name == "riser":
        sec = d or 1.5
        tt = t_(sec)
        y = band(rng.standard_normal(len(tt)), 800, 8000) * (tt / sec) ** 2 * 0.5
        y += np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt / sec) ** 2) / SR) * (tt / sec) ** 2 * 0.3
        return y * 0.5
    if name == "hit":
        w = boom(1.8)
        return w * 0.9 + band(rng.standard_normal(len(w)), 60, 3000) * np.exp(-t_(1.8) * 9) * 0.4
    if name == "heart":
        y = _silence(0.8)
        put(y, kick(0.25), 0)
        put(y, kick(0.25), 0.22, 0.7)
        return y * 0.7
    if name == "gasp":
        y = _silence(0.7)
        for _ in range(10):
            g = band(rng.standard_normal(int(SR * 0.45)), rng.uniform(700, 1000), rng.uniform(2200, 3200))
            put(y, g * np.sin(np.pi * t_(0.45) / 0.45) ** 3, rng.uniform(0, 0.2))
        return y / (np.abs(y).max() + 1e-9) * 0.35
    if name == "glitch":  # AI대리 화면이 지지직
        sec = d or 0.6
        y = band(rng.standard_normal(int(SR * sec)), 1500, 9000)
        gate = (np.sin(2 * np.pi * 23 * t_(sec)) > 0.2).astype(float)
        return y * gate * 0.3
    raise ValueError(f"모르는 효과음: {name}")


SFX = ("ding", "code", "unlock", "steps", "sip", "murmur", "riser", "hit", "heart", "gasp", "glitch")
