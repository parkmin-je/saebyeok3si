"""장면별 배경음악(큐) 합성: 외부 음원 없이 코드로 만든 자체 음원이라 저작권 걱정이 없다.

큐 종류
- tension : 긴장 (폰이 깨지는 오프닝). 낮은 심장박동 킥, 16분 하이햇, 단조 드론, 상승 노이즈.
- banter  : 밀당 (둘이 맞붙는 장면). 통통 튀는 피치카토 리프, 핑거스냅, 워킹 베이스. 장난스러운 도리안.
- flutter : 설렘 (창가에서 웃음 참는 장면). 밝은 일렉피아노 화음, 부드러운 킥·셰이커, 반짝이는 벨 멜로디.
- stop    : 음악을 끊는다 (반전 직전 정적).
compose_cues([{"t": 0, "type": "tension"}, {"t": 6.2, "type": "banter"}, ...], total) → mono float (SR=48000)
"""
import numpy as np

SR = 48000
A4 = 440.0
NOTE = {"C": -9, "C#": -8, "Db": -8, "D": -7, "D#": -6, "Eb": -6, "E": -5, "F": -4, "F#": -3, "Gb": -3,
        "G": -2, "G#": -1, "Ab": -1, "A": 0, "A#": 1, "Bb": 1, "B": 2}


def hz(n: str) -> float:
    name, octv = n[:-1], int(n[-1])
    return A4 * 2 ** ((NOTE[name] + 12 * (octv - 4)) / 12)


def _t(sec):
    return np.arange(int(SR * sec)) / SR


# ---------- 악기 ----------
def kick(vel=1.0, tight=1.0):
    t = _t(0.45)
    f = 45 + 110 * np.exp(-t * 28 * tight)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7 * tight) * vel


def snap(vel=1.0, rng=None):
    rng = rng or np.random.default_rng(1)
    t = _t(0.18)
    n = rng.standard_normal(len(t))
    n = n - np.convolve(n, np.ones(6) / 6, "same")   # 고역만
    return n * np.exp(-t * 38) * vel * 0.6


def hat(vel=1.0, rng=None, open_=False):
    rng = rng or np.random.default_rng(2)
    t = _t(0.25 if open_ else 0.06)
    n = rng.standard_normal(len(t))
    n = n - np.convolve(n, np.ones(3) / 3, "same")
    return n * np.exp(-t * (18 if open_ else 80)) * vel * 0.25


def shaker(vel=1.0, rng=None):
    rng = rng or np.random.default_rng(3)
    t = _t(0.12)
    env = np.sin(np.pi * np.minimum(1, t / 0.12)) ** 2
    n = rng.standard_normal(len(t))
    n = n - np.convolve(n, np.ones(4) / 4, "same")
    return n * env * vel * 0.12


def pluck(f, dur=0.3, vel=1.0):
    """피치카토·기타 느낌 (카플러스-스트롱 근사: 배음이 빨리 줄어듦)."""
    t = _t(dur + 0.4)
    out = np.zeros(len(t))
    for k in range(1, 8):
        out += np.sin(2 * np.pi * f * k * t) * np.exp(-t * (6 + 5 * k)) / k
    return out * np.minimum(1, t / 0.003) * vel


def epiano(f, dur, vel=1.0):
    """일렉 피아노(로즈 느낌): FM 종소리 배음 + 부드러운 감쇠 + 트레몰로."""
    t = _t(dur + 1.2)
    mod = np.sin(2 * np.pi * f * 14 * t) * 0.9 * np.exp(-t * 9)
    car = np.sin(2 * np.pi * f * t + mod) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    env = np.minimum(1, t / 0.005) * np.exp(-t * 1.6) * np.where(t > dur, np.exp(-(t - dur) * 5), 1)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    return car * env * trem * vel


def bell(f, dur=0.6, vel=1.0):
    t = _t(dur + 1.5)
    out = np.zeros(len(t))
    for r, a, d in ((1, 1, 2.5), (2, .4, 4), (2.76, .25, 6), (5.4, .1, 9)):
        out += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d)
    return out * np.minimum(1, t / 0.002) * vel


def bass(f, dur, vel=1.0):
    t = _t(dur + 0.15)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    env = np.minimum(1, t / 0.008) * np.where(t > dur, np.exp(-(t - dur) * 30), np.exp(-t * 1.5))
    return s * env * vel


def pad(freqs, dur, vel=1.0):
    t = _t(dur)
    out = np.zeros(len(t))
    for f in freqs:
        for det in (-0.12, 0.0, 0.12):   # 살짝 어긋난 톱니파 겹치기 → 현악 패드
            ph = (f * 2 ** (det / 12) * t) % 1
            out += (2 * ph - 1) * 0.3
    out = np.convolve(out, np.ones(40) / 40, "same")   # 고역 깎기
    env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.4).clip(0)
    return out * env * vel / max(1, len(freqs))


def riser(dur, vel=1.0, rng=None):
    rng = rng or np.random.default_rng(4)
    t = _t(dur)
    n = rng.standard_normal(len(t))
    out = np.zeros(len(t))
    # 점점 밝아지는 노이즈 (구간별로 저역통과 폭을 줄임)
    for i, w in enumerate(np.linspace(60, 4, 8)):
        a, b = i * len(t) // 8, (i + 1) * len(t) // 8
        out[a:b] = np.convolve(n, np.ones(int(w)) / int(w), "same")[a:b]
    return out * (t / dur) ** 2 * vel


def reverb(x, sec=1.6, wet=0.3, seed=5):
    rng = np.random.default_rng(seed)
    t = _t(sec)
    ir = rng.standard_normal(len(t)) * np.exp(-t * 4)
    ir = np.convolve(ir, np.ones(20) / 20, "same")
    ir = ir / np.abs(ir).sum() * 12
    n = len(x) + len(ir) - 1
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
    return x * (1 - wet) + y * wet


# ---------- 큐 ----------
class Track:
    def __init__(self, sec):
        self.x = np.zeros(int(SR * (sec + 2)))

    def add(self, sig, at, gain=1.0):
        i = int(at * SR)
        if i >= len(self.x) or i < 0:
            return
        j = min(len(self.x), i + len(sig))
        self.x[i:j] += sig[:j - i] * gain


def cue_tension(sec, seed=0):
    rng = np.random.default_rng(seed)
    bpm, tr = 100, Track(sec)
    beat = 60 / bpm
    tr.add(pad([hz("A2"), hz("E3"), hz("C4")], sec + 1, 0.5), 0)
    tr.add(riser(min(1.2, sec), 0.35, rng), 0)
    b = 0
    while b * beat < sec:
        t0 = b * beat
        if b % 4 == 0:
            tr.add(kick(1.0), t0)
            tr.add(kick(0.6), t0 + beat * 0.5)          # 심장박동 두 번
        for s in range(4):
            tr.add(hat(0.5 + 0.3 * (s == 0), rng), t0 + s * beat / 4)
        if b % 2 == 1:
            tr.add(pluck(hz("A2") * (1.5 if b % 8 == 7 else 1), beat * 0.4, 0.5), t0)
        b += 1
    return tr.x[:int(sec * SR)]


def cue_banter(sec, seed=0):
    """장난스러운 밀당: D 도리안 피치카토 리프 + 스냅 + 통통 베이스."""
    rng = np.random.default_rng(seed)
    bpm, tr = 116, Track(sec)
    beat = 60 / bpm
    riff = ["D4", "F4", "A4", "B4", "A4", "F4", "G4", "E4"]
    bassline = ["D2", "D2", "A2", "D2", "G2", "G2", "A2", "C3"]
    b = 0
    while b * beat < sec:
        t0 = b * beat
        sw = beat * 0.58                               # 스윙
        tr.add(pluck(hz(riff[(2 * b) % 8]), 0.18, 0.55), t0)
        tr.add(pluck(hz(riff[(2 * b + 1) % 8]), 0.18, 0.45), t0 + sw)
        tr.add(bass(hz(bassline[b % 8]), beat * 0.45, 0.7), t0)
        if b % 2 == 1:
            tr.add(snap(0.9, rng), t0)
        if b % 2 == 0:
            tr.add(kick(0.55, 1.6), t0)
        if b % 8 == 6:
            tr.add(bell(hz("A5"), 0.2, 0.18), t0 + sw)  # 장난스러운 '띵'
        b += 1
    return reverb(tr.x, 0.8, 0.18)[:int(sec * SR)]


def cue_flutter(sec, seed=0):
    """설렘: C-G-Am-F 일렉피아노 + 부드러운 비트 + 벨 멜로디."""
    rng = np.random.default_rng(seed)
    bpm, tr = 92, Track(sec)
    beat = 60 / bpm
    prog = [("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "G4", "B4"]), ("A2", ["E4", "A4", "C5"]), ("F2", ["F4", "A4", "C5"])]
    mel = [["E5", "G5", "C6", "B5"], ["D6", "B5", "G5", None], ["C6", "E6", "D6", "C6"], ["A5", None, "G5", None]]
    bar = 4 * beat
    m = 0
    while m * bar < sec:
        t0 = m * bar
        root, ch = prog[m % 4]
        tr.add(bass(hz(root), bar * 0.9, 0.55), t0)
        for k in (0, 1.5, 2, 3):                        # 싱코페이션 컴핑
            for c in ch:
                tr.add(epiano(hz(c), beat * 0.8, 0.22), t0 + k * beat + rng.normal(0, 0.006))
        for k in range(4):
            tr.add(kick(0.45, 1.3), t0 + k * beat) if k in (0, 2) else tr.add(snap(0.35, rng), t0 + k * beat)
            tr.add(shaker(0.8, rng), t0 + k * beat + beat / 2)
        if m >= 1:
            for k, n in enumerate(mel[m % 4]):
                if n:
                    tr.add(bell(hz(n), beat * 0.8, 0.22), t0 + k * beat)
        m += 1
    return reverb(tr.x, 1.8, 0.3)[:int(sec * SR)]


CUES = {"tension": cue_tension, "banter": cue_banter, "flutter": cue_flutter}


def compose_cues(cues, total, xfade=0.25):
    n = int(total * SR)
    out = np.zeros(n)
    cues = sorted(cues, key=lambda c: c["t"])
    for i, c in enumerate(cues):
        s = c["t"]
        e = cues[i + 1]["t"] if i + 1 < len(cues) else total
        if c["type"] == "stop" or e <= s:
            continue
        seg = CUES[c["type"]](e - s + xfade, seed=i) * float(c.get("gain", 1.0))
        seg = seg / (np.abs(seg).max() + 1e-9) * 0.8
        fi, fo = int(0.04 * SR), int(xfade * SR)
        seg[:fi] *= np.linspace(0, 1, fi)
        seg[-fo:] *= np.linspace(1, 0, fo)
        a = int(s * SR)
        b = min(n, a + len(seg))
        out[a:b] += seg[:b - a]
    return out
