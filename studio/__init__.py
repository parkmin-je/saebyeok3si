"""콩사원 AI 생존기 제작기.

대본(JSON) + 채널 설정(series/<채널>/channel.json) → 목소리 → 타임라인·자막 → 음악·효과음 → 세로 렌더 → mp4.
실행: python -m studio --help
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = Path(__file__).resolve().parent / "web"
