"""ffmpeg/ffprobe 헬퍼."""
import json
import subprocess
from pathlib import Path

from .errors import FatalError


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise FatalError(f"{cmd[0]} 실패: {p.stderr[-2000:]}")


def probe(path: Path) -> dict:
    p = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
                        "-show_streams", str(path)], capture_output=True, text=True)
    if p.returncode != 0:
        raise FatalError(f"ffprobe 실패: {path}: {p.stderr}")
    return json.loads(p.stdout)


def duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def has_audio(path: Path) -> bool:
    return any(s["codec_type"] == "audio" for s in probe(path)["streams"])
