"""테스트·드라이런용 가짜 공급자. 결정적 출력, 외부 호출 없음."""
import subprocess
import tempfile
from pathlib import Path

from .base import VoiceSpec


def _ff(args: list[str], out_ext: str) -> bytes:
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / f"o.{out_ext}"
        subprocess.run(["ffmpeg", "-y", "-v", "error", *args, str(out)], check=True)
        return out.read_bytes()


class FakeImage:
    name = "fake:image"

    def generate(self, prompt, negative, width, height, seed, reference_images=None):
        color = f"0x{(seed * 2654435761) & 0xFFFFFF:06x}"
        return _ff(["-f", "lavfi", "-i", f"color=c={color}:s={width}x{height}", "-frames:v", "1"], "png"), 0.0


class FakeVideo:
    name = "fake:video"

    def animate(self, image, prompt, negative, duration_sec, seed):
        return _ff(["-loop", "1", "-i", str(image), "-f", "lavfi", "-i", "anoisesrc=a=0.01",
                    "-t", str(duration_sec), "-vf", "scale=1080:1920,zoompan=z='1+0.0008*on':d=1:s=1080x1920:fps=24",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"], "mp4"), 0.0


class FakeTTS:
    name = "fake:tts"

    def synthesize(self, text: str, voice: VoiceSpec):
        sec = max(0.6, len(text.replace(" ", "")) / 6.0)
        return _ff(["-f", "lavfi", "-i", f"sine=f=220:d={sec:.2f}", "-ar", "48000", "-ac", "1"], "wav"), 0.0
