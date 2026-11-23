"""무료 CPU에서 생성 컷 화질 올리기: Real-ESRGAN(general x4v3, BSD) 4배 업스케일 + GFPGAN v1.4(Apache) 얼굴 복원.

사용: python enhance_clips.py <clip.mp4> <out.mp4>
- 프레임마다 4배 → 세로 1920 기준으로 줄임 (작은 원본보다 머리카락·눈·교복 질감이 또렷)
- 얼굴(정면 검출)은 GFPGAN 결과를 타원 마스크로 55% 섞음 (100%면 인형 같아져서)
"""
import subprocess, sys, tempfile, urllib.request
from pathlib import Path

import cv2
import numpy as np
import torch
from spandrel import ModelLoader

torch.set_num_threads(4)
CACHE = Path.home() / ".cache" / "rrs-models"
URLS = {
    "esr": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth",
    "gfp": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
}


def load(name):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / Path(URLS[name]).name
    if not f.exists():
        urllib.request.urlretrieve(URLS[name], f)
    return ModelLoader().load_from_file(str(f)).model.eval()


def run(src, dst, out_h=1920, face_mix=0.55):
    esr, gfp = load("esr"), load("gfp")
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    cap = cv2.VideoCapture(src)
    tmp = Path(tempfile.mkdtemp())
    i = 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype("float32") / 255.0
        with torch.no_grad():
            t = torch.from_numpy(rgb).permute(2, 0, 1)[None]
            up = esr(t)[0].permute(1, 2, 0).clamp(0, 1).numpy()
        h = out_h
        w = int(round(up.shape[1] * h / up.shape[0] / 2)) * 2
        img = cv2.resize((up * 255).astype("uint8"), (w, h), interpolation=cv2.INTER_AREA)
        g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        for (x, y, fw, fh) in casc.detectMultiScale(g, 1.1, 6, minSize=(90, 90)):
            cx, cy, sz = x + fw // 2, y + fh // 2, int(max(fw, fh) * 1.6)
            x0, y0 = max(0, cx - sz // 2), max(0, cy - sz // 2)
            x1, y1 = min(w, x0 + sz), min(h, y0 + sz)
            crop = cv2.resize(img[y0:y1, x0:x1], (512, 512), interpolation=cv2.INTER_AREA)
            with torch.no_grad():
                r = gfp(torch.from_numpy(crop.astype("float32") / 255.0).permute(2, 0, 1)[None] * 2 - 1)
                r = (r[0] if isinstance(r, (tuple, list)) else r)[0]
                r = ((r + 1) / 2).permute(1, 2, 0).clamp(0, 1).numpy()
            r = cv2.resize((r * 255).astype("uint8"), (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
            m = np.zeros((y1 - y0, x1 - x0), "float32")
            cv2.ellipse(m, ((x1 - x0) // 2, (y1 - y0) // 2), (int((x1 - x0) * .34), int((y1 - y0) * .42)), 0, 0, 360, 1, -1)
            m = cv2.GaussianBlur(m, (0, 0), (x1 - x0) * .06)[..., None] * face_mix
            img[y0:y1, x0:x1] = (img[y0:y1, x0:x1] * (1 - m) + r * m).astype("uint8")
        cv2.imwrite(str(tmp / f"{i:05d}.png"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        i += 1
        if i % 10 == 0:
            print(f"  {Path(src).name} {i} 프레임", flush=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", fps or "16", "-i", str(tmp / "%05d.png"),
                    "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", dst], check=True)
    print(f"[enhance] {src} → {dst} ({i} 프레임)", flush=True)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
