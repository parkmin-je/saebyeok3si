"""배경음악: 외부 서비스 없이 코드로 합성한 피아노 왈츠 (저작권 걱정 없는 자체 음원).

느린 3/4 왈츠, 가단조 진행. 피아노 음색은 감쇠하는 배음 합성, 공간감은 합성 잔향(IR 컨볼루션),
시대감은 LP 잡음(크래클)으로 낸다. 같은 seed면 같은 음악이 나온다.
"""
import wave

import numpy as np

from .common import Ctx

name = "music"
SR = 48000
A4 = 440.0
NOTE = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}


def hz(n: str) -> float:
    name, octv = n[:-1], int(n[-1])
    return A4 * 2 ** ((NOTE[name] + 12 * (octv - 4)) / 12)


def piano(f: float, dur: float, vel: float) -> np.ndarray:
    n = int(SR * (dur + 2.5))
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)  # 약한 비조화성
        if fk > SR / 2.2:
            break
        decay = 1.2 + 0.7 * k + f / 600
        out += (1 / k ** 1.4) * np.sin(2 * np.pi * fk * t + k) * np.exp(-t * decay)
    att = np.minimum(1, t / 0.006)
    rel = np.where(t > dur, np.exp(-(t - dur) * 6), 1.0)  # 건반에서 손 떼면 빨리 줄어듦
    return out * att * rel * vel


def reverb_ir(sec: float, rng) -> np.ndarray:
    n = int(SR * sec)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 3.2)
    ir = np.convolve(ir, np.ones(24) / 24, mode="same")  # 고역을 조금 깎아 따뜻하게
    ir[0] = 1.0
    return ir / np.abs(ir).sum() * 18


def fft_convolve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = len(a) + len(b) - 1
    size = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, size) * np.fft.rfft(b, size), size)[:n]


PROG = [  # (베이스, 화음) 한 마디씩
    ("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"]), ("C3", ["G3", "C4", "E4"]), ("G2", ["G3", "B3", "D4"]),
    ("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"]), ("D3", ["F3", "A3", "D4"]), ("E2", ["G#3", "B3", "E4"]),
]
MELODY = [  # 마디별 오른손 (음, 시작 박, 길이 박)
    [("E5", 0, 2), ("D5", 2, 1)], [("C5", 0, 3)], [("E5", 0, 1), ("G5", 1, 1), ("E5", 2, 1)], [("D5", 0, 3)],
    [("E5", 0, 2), ("A5", 2, 1)], [("G5", 0, 1.5), ("F5", 1.5, 1.5)], [("F5", 0, 1), ("E5", 1, 1), ("D5", 2, 1)], [("B4", 0, 3)],
]


def compose(total_sec: float, bpm: float = 66, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = 3 * beat
    n = int(SR * (total_sec + 3))
    mix = np.zeros(n)

    def add(sig, at):
        i = int(at * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        mix[i:j] += sig[: j - i]

    bars = int(np.ceil(total_sec / bar)) + 1
    for b in range(bars):
        t0 = b * bar
        bass, chord = PROG[b % len(PROG)]
        intro = b < 2  # 처음 두 마디는 오른손 없이 조용히
        human = lambda: rng.normal(0, 0.012)
        add(piano(hz(bass), bar * 0.95, 0.55), t0 + human())
        for k in (1, 2):
            for c in chord:
                add(piano(hz(c), beat * 0.9, 0.16), t0 + k * beat + human())
        if not intro:
            for note, st, ln in MELODY[b % len(MELODY)]:
                octave_down = b >= 10 and b % 8 in (4, 5)  # 두 번째 반복은 살짝 변주
                f = hz(note) / (2 if octave_down else 1)
                add(piano(f, ln * beat * 0.95, 0.42), t0 + st * beat + human())
    mix = fft_convolve(mix, reverb_ir(2.6, rng))[:n] * 0.6 + mix * 0.55

    # LP 잡음: 낮은 히스 + 드문 크래클
    hiss = np.convolve(rng.standard_normal(n), np.ones(40) / 40, mode="same") * 0.004
    clicks = np.zeros(n)
    idx = rng.choice(n, size=int(total_sec * 9), replace=False)
    clicks[idx] = rng.uniform(-0.05, 0.05, len(idx))
    clicks = np.convolve(clicks, np.hanning(30), mode="same")
    mix = mix + hiss + clicks

    fade = np.ones(n)
    end = int(total_sec * SR)
    fl = int(2.0 * SR)
    fade[end - fl:end] = np.linspace(1, 0, fl)
    fade[end:] = 0
    mix = (mix * fade)[:end]
    return mix / (np.abs(mix).max() + 1e-9) * 0.7


def write_wav(path, x: np.ndarray) -> None:
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def run(ctx: Ctx, total_sec: float) -> None:
    p = ctx.run_dir / "audio" / "bgm.wav"
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name("bgm.tmp.wav")
    write_wav(tmp, compose(total_sec))
    tmp.replace(p)
    ctx.log(f"[music] 피아노 왈츠 {total_sec:.1f}s 합성")
