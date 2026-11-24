"""코드로 만드는 악기 (외부 음원이 없어 저작권 걱정이 없다). 모두 48kHz 모노 float."""

import numpy as np

SR = 48000
_A4 = 440.0
_NOTE = {
    "C": -9,
    "C#": -8,
    "Db": -8,
    "D": -7,
    "D#": -6,
    "Eb": -6,
    "E": -5,
    "F": -4,
    "F#": -3,
    "Gb": -3,
    "G": -2,
    "G#": -1,
    "Ab": -1,
    "A": 0,
    "A#": 1,
    "Bb": 1,
    "B": 2,
}


def hz(n: str) -> float:
    """음 이름(예: "C#4") → 주파수."""
    name, octv = n[:-1], int(n[-1])
    return _A4 * 2 ** ((_NOTE[name] + 12 * (octv - 4)) / 12)


def t_(sec: float) -> np.ndarray:
    return np.arange(int(SR * sec)) / SR


def epiano(f, dur, vel=1.0):
    """일렉 피아노: FM 종소리 배음 + 부드러운 감쇠 + 트레몰로."""
    t = t_(dur + 1.2)
    mod = np.sin(2 * np.pi * f * 14 * t) * 0.9 * np.exp(-t * 9)
    car = np.sin(2 * np.pi * f * t + mod) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    env = np.minimum(1, t / 0.005) * np.exp(-t * 1.6) * np.where(t > dur, np.exp(-(t - dur) * 5), 1)
    return car * env * (1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)) * vel


def bell(f, dur=0.6, vel=1.0):
    t = t_(dur + 1.5)
    out = np.zeros(len(t))
    for r, a, d in ((1, 1, 2.5), (2, 0.4, 4), (2.76, 0.25, 6), (5.4, 0.1, 9)):
        out += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d)
    return out * np.minimum(1, t / 0.002) * vel


def bass(f, dur, vel=1.0):
    t = t_(dur + 0.15)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    env = np.minimum(1, t / 0.008) * np.where(t > dur, np.exp(-(t - dur) * 30), np.exp(-t * 1.5))
    return s * env * vel


def pad(freqs, dur, vel=1.0):
    """살짝 어긋난 톱니파를 겹친 현악 패드."""
    t = t_(dur)
    out = np.zeros(len(t))
    for f in freqs:
        for det in (-0.12, 0.0, 0.12):
            ph = (f * 2 ** (det / 12) * t) % 1
            out += (2 * ph - 1) * 0.3
    out = np.convolve(out, np.ones(40) / 40, "same")
    env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.4).clip(0)
    return out * env * vel / max(1, len(freqs))


def kick(sec=0.35):
    t = t_(sec)
    f = 50 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def clap(rng, sec=0.18):
    t = t_(sec)
    x = rng.standard_normal(len(t)) * np.exp(-t * 28)
    return x - np.convolve(x, np.ones(6) / 6, "same")


def whoosh(rng, sec=0.32):
    t = t_(sec)
    x = rng.standard_normal(len(t))
    x = np.convolve(x, np.ones(18) / 18, "same") - np.convolve(x, np.ones(90) / 90, "same")
    return x * np.sin(np.pi * t / sec) ** 2


def boom(sec=1.6):
    t = t_(sec)
    f = 38 + 60 * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)


def band(x, lo, hi):
    """FFT로 lo~hi Hz만 남긴다."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(spec, len(x))


def tone(f, sec, decay=8, harm=(1, 0.3)):
    t = t_(sec)
    return sum(a * np.sin(2 * np.pi * f * (k + 1) * t) for k, a in enumerate(harm)) * np.exp(-t * decay)


def reverb(x, sec=1.6, wet=0.3, seed=5):
    rng = np.random.default_rng(seed)
    t = t_(sec)
    ir = np.convolve(rng.standard_normal(len(t)) * np.exp(-t * 4), np.ones(20) / 20, "same")
    ir = ir / np.abs(ir).sum() * 12
    n = len(x) + len(ir) - 1
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return x * (1 - wet) + y * wet


def put(buf: np.ndarray, sig: np.ndarray, at: float, gain=1.0) -> None:
    """buf 의 at초 위치에 sig 를 더한다 (끝을 넘는 부분은 버림)."""
    i = int(at * SR)
    if i < 0 or i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain
