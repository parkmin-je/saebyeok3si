"""소리 섞기 (목소리 + 음악 + 효과음) 와 그림 촬영·인코딩."""

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from . import WEB
from .music import MOODS, sfx
from .synth import SR, bell, boom, hz, put, whoosh
from .voice import read_wav


def load_voice(path) -> np.ndarray:
    """wav → 48kHz float (선형 보간)."""
    x, sr = read_wav(path)
    if sr == SR:
        return x.astype(np.float64)
    n = int(len(x) * SR / sr)
    return np.interp(np.arange(n) * sr / SR, np.arange(len(x)), x)


def mute_mask(tl: dict, n: int) -> np.ndarray:
    """효과음 'silence' 구간은 배경음을 완전히 죽인다 (0.15초에 걸쳐 부드럽게). 정적 뒤 한 방을 위해."""
    m = np.ones(n)
    for sh in tl["shots"]:
        for ev in sh.get("sfx", []):
            if ev[0] == "silence":
                a = int((sh["start"] + ev[1]) * SR)
                m[max(0, a): max(0, a + int((ev[2] if len(ev) > 2 else 1.0) * SR))] = 0
    k = int(SR * 0.15)
    return np.convolve(m, np.ones(k) / k, "same")


def mix(tl: dict) -> np.ndarray:
    total = tl["total"]
    n = int(total * SR)
    voice = np.zeros(n)
    for c in tl["caps"]:
        if "wav" in c:
            v = load_voice(c["wav"])
            put(voice, v / (np.abs(v).max() + 1e-9) * 0.9, c["start"])
    mus = MOODS[tl.get("mood") or "bright"](total, tl["soft_from"])
    speak = (np.abs(voice) > 0.02).astype(float)
    duck = np.convolve(speak, np.ones(int(SR * 0.3)) / (SR * 0.3), "same")  # 말할 때 음악 낮춤
    mus = mus[:n] * 0.32 * (1 - 0.55 * np.clip(duck * 3, 0, 1))
    mus *= mute_mask(tl, n)
    horror = tl.get("mood") == "dread"
    fx = np.zeros(n)
    rng = np.random.default_rng(3)
    for c in [] if horror else tl["cuts"][1:]:  # 휙 소리는 코미디용
        put(fx, whoosh(rng), c - 0.16, 0.22)
    for s in tl["stages"]:
        put(fx, bell(hz("G5"), 0.6, 0.3) + bell(hz("C6"), 0.6, 0.25), s, 0.5)
        if tl.get("mood") == "mystery":
            put(fx, boom(), s, 0.7)
    for sh in tl["shots"]:
        for ev in sh.get("sfx", []):
            put(fx, sfx(ev[0], ev[2] if len(ev) > 2 else None, rng), sh["start"] + ev[1])
    if not horror:
        put(fx, bell(hz("E5"), 0.5, 0.3), tl["card"]["start"], 0.4)
    out = voice + mus + fx
    fade = int(SR * 1.2)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out / (np.abs(out).max() + 1e-9) * 0.92


def write_timeline(tl: dict, work: Path) -> Path:
    p = work / "timeline.json"
    p.write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    return p


def capture(tl: dict, work: Path, out: Path, mode="full", *, start=None, end=None) -> None:
    args = ["node", str(WEB / "capture.js"), str(write_timeline(tl, work)), str(out), mode]
    if start is not None:
        args += [f"{start:.3f}", f"{end:.3f}"]
    subprocess.run(args, check=True, env={**os.environ, "ENGINE": str(WEB / "engine.html")})


def frames(tl: dict, work: Path, jobs: int) -> Path:
    out = work / "frames"
    out.mkdir(exist_ok=True)
    cuts = np.linspace(0, tl["total"], jobs + 1)
    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(lambda k: capture(tl, work, out, "full", start=cuts[k], end=cuts[k + 1]), range(jobs)))
    return out


def stills(tl: dict, work: Path, times: list[float]) -> list[Path]:
    """미리보기 그림 몇 장 (컷 확인용)."""
    out = work / "stills"
    capture(tl, work, out, ",".join(f"{t:.3f}" for t in times))
    return sorted(out.glob("*.jpg"))


def encode(work: Path, audio: np.ndarray, out: Path, preview: Path | None = None) -> None:
    (work / "mix.f32").write_bytes(audio.astype(np.float32).tobytes())
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-framerate",
            "30",
            "-i",
            str(work / "frames" / "%06d.jpg"),
            "-f",
            "f32le",
            "-ar",
            str(SR),
            "-ac",
            "1",
            "-i",
            str(work / "mix.f32"),
            "-af",
            "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:v",
            "libx264",
            "-crf",
            "19",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out),
        ],
        check=True,
    )
    if preview:  # 휴대폰으로 보기 좋은 720p (10MB 안팎)
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-i",
                str(out),
                "-vf",
                "scale=720:-2",
                "-c:v",
                "libx264",
                "-crf",
                "26",
                "-preset",
                "medium",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(preview),
            ],
            check=True,
        )
