"""실사 사진을 움직이는 장면으로: 깊이 지도 기반 2.5D 시차(parallax) 카메라.

가까운 것은 더 많이, 먼 것은 덜 움직여서 정지 사진이 입체적으로 살아 움직이는 느낌을 낸다.
(바이럴 쇼츠에서 흔히 쓰는 '3D 사진' 효과. 외부 서비스 없이 OpenCV remap으로 처리)
"""
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

W, H, FPS = 1080, 1920, 30

MOTIONS = {  # 장면 진행률 p(0~1)에 따른 (줌, 가로 이동px, 세로 이동px). 이동량은 가까운 곳 기준
    "push_in": lambda p: (1.0 + 0.10 * p, 0, -10 * p),
    "zoom_in": lambda p: (1.0 + 0.10 * p, 0, 0),
    "zoom_out": lambda p: (1.10 - 0.10 * p, 0, 0),
    "pan_left": lambda p: (1.06, 40 - 80 * p, 0),
    "pan_right": lambda p: (1.06, -40 + 80 * p, 0),
    "orbit": lambda p: (1.05 + 0.03 * p, 45 * math.sin(p * math.pi - math.pi / 2), 8 * math.sin(p * math.pi)),
}


def motion_for(prompt: str) -> str:
    p = (prompt or "").lower()
    for key, name in (("push", "push_in"), ("zoom out", "zoom_out"), ("pull", "zoom_out"), ("pan left", "pan_left"),
                      ("pan right", "pan_right"), ("zoom", "zoom_in"), ("orbit", "orbit")):
        if key in p:
            return name
    return "orbit"


def fit_cover(img: np.ndarray) -> np.ndarray:
    """9:16로 꽉 차게 자르고 1080x1920 + 여유(줌 대비 8%)로 맞춘다."""
    h, w = img.shape[:2]
    target = W / H
    if w / h > target:
        nw = int(h * target)
        img = img[:, (w - nw) // 2:(w - nw) // 2 + nw]
    else:
        nh = int(w / target)
        img = img[(h - nh) // 2:(h - nh) // 2 + nh]
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)


def render_scene(image: Path, depth: np.ndarray | None, seconds: float, motion: str, out_mp4: Path,
                 strength: float = 1.0) -> None:
    img = fit_cover(cv2.imread(str(image), cv2.IMREAD_COLOR))
    if depth is None:
        d = np.tile(np.linspace(0.2, 1.0, H, dtype=np.float32)[:, None], (1, W))  # 아래가 가깝다고 가정
    else:
        d = cv2.resize(fit_cover(cv2.cvtColor(depth, cv2.COLOR_GRAY2BGR))[:, :, 0], (W, H)).astype(np.float32)
        d = (d - d.min()) / max(1e-6, d.max() - d.min())
    d = cv2.GaussianBlur(d, (0, 0), 6)  # 경계 찢어짐 완화
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H / 2
    n = max(1, round(seconds * FPS))
    fn = MOTIONS.get(motion, MOTIONS["orbit"])
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                           "-pix_fmt", "yuv420p", str(out_mp4)], stdin=subprocess.PIPE)
    for i in range(n):
        p = i / max(1, n - 1)
        p = p * p * (3 - 2 * p)
        zoom, dx, dy = fn(p)
        # 깊이별 줌: 가까운 곳(d=1)은 zoom 그대로, 먼 곳(d=0)은 절반만 → 돌리 느낌
        z = 1 + (zoom - 1) * (0.5 + 0.5 * d) * strength
        mx = cx + (xs - cx) / z - dx * d * strength
        my = cy + (ys - cy) / z - dy * d * strength
        # 화면 가장자리 빈 곳이 안 보이게 전체를 살짝 확대
        mx = cx + (mx - cx) / 1.06
        my = cy + (my - cy) / 1.06
        frame = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg parallax 인코딩 실패")
