"""공급자 어댑터 인터페이스 (INTERFACES.md §5).

VideoProvider는 ARCHITECTURE.md §10의 확장(S3b: 이미지→영상 클립)을 위해 추가했다.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class VoiceSpec:
    description: str      # 대본의 voice 문장 ("70대 여성, 낮고 차분한 목소리")
    voice_id: str         # 공급자 voice 이름
    speed: float = 1.0


class ImageProvider(Protocol):
    name: str

    def generate(self, prompt: str, negative: str, width: int, height: int,
                 seed: int, reference_images: list[Path] | None = None) -> tuple[bytes, float]: ...


class VideoProvider(Protocol):
    name: str

    def animate(self, image: Path, prompt: str, negative: str, duration_sec: int,
                seed: int) -> tuple[bytes, float]: ...
    # 9:16 mp4 바이트. 공급자가 오디오(환경음)를 같이 줄 수 있다


class TTSProvider(Protocol):
    name: str

    def synthesize(self, text: str, voice: VoiceSpec) -> tuple[bytes, float]: ...
    # WAV 48kHz mono
