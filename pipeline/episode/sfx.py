"""효과음을 코드로 합성 (저작권 걱정 없음). 48kHz mono float."""
import numpy as np

SR = 48000


def _env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)


def crack(sec=0.5):
    n = int(SR * sec)
    noise = np.random.default_rng(1).standard_normal(n)
    hit = noise * _env(n, 0.001, 0.05)
    thump = np.sin(2 * np.pi * 70 * np.arange(n) / SR) * _env(n, 0.002, 0.12)
    return 0.8 * hit + 0.9 * thump


def whoosh(sec=0.6):
    n = int(SR * sec)
    noise = np.random.default_rng(2).standard_normal(n)
    k = np.hanning(n)
    # 점점 높아지는 대역 느낌: 이동 평균 폭을 줄여 간다
    out = np.convolve(noise, np.ones(30) / 30, "same") * k
    return 0.6 * out / (np.abs(out).max() + 1e-9)


def buzz(sec=1.2):
    """폴더폰 진동: 175Hz 웅웅 0.25초 x 3"""
    n = int(SR * sec)
    t = np.arange(n) / SR
    gate = ((t % 0.4) < 0.25).astype(float)
    return 0.5 * np.sign(np.sin(2 * np.pi * 175 * t)) * gate * 0.6


def heartbeat(sec=1.6):
    n = int(SR * sec)
    out = np.zeros(n)
    for start in (0.0, 0.25, 0.8, 1.05):
        s = int(start * SR)
        m = min(n - s, int(0.18 * SR))
        out[s:s + m] += np.sin(2 * np.pi * 55 * np.arange(m) / SR) * _env(m, 0.003, 0.05)
    return 0.9 * out


def sting(sec=1.5):
    """떡밥 엔딩용 낮은 현악 느낌 스팅"""
    n = int(SR * sec)
    t = np.arange(n) / SR
    tone = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate((110, 164.8, 220, 233.1)))
    return 0.25 * tone * np.minimum(1, t / 0.05) * np.exp(-t / 0.9)


BANK = {"crack": crack, "whoosh": whoosh, "buzz": buzz, "heartbeat": heartbeat, "sting": sting}
