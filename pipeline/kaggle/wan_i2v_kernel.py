"""Kaggle 무료 GPU에서 도는 커널 본체 (템플릿). run_kaggle.py가 JOBS를 채워 넣어 push한다.

Wan 2.2 TI2V-5B (Apache-2.0): 인물 사진 한 장 + 동작 문장 → 5초 안팎 실사 영상.
결과: /kaggle/working/<name>.mp4
"""
import base64, io, json, os, subprocess, sys, time

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.1", "transformers>=4.49",
                "accelerate", "ftfy", "imageio", "imageio-ffmpeg", "spandrel", "opencv-python-headless"], check=True)
import torch  # noqa: E402
from diffusers import AutoencoderKLWan, WanImageToVideoPipeline  # noqa: E402
from diffusers.utils import export_to_video  # noqa: E402
from PIL import Image  # noqa: E402

JOBS = json.loads(base64.b64decode("__JOBS__").decode())   # [{name, prompt, image_b64, frames}]
MODEL = os.environ.get("WAN_MODEL", "Wan-AI/Wan2.2-TI2V-5B-Diffusers")
NEG = ("blurry, low quality, deformed face, extra limbs, fused bodies, distorted hands, text, watermark, "
       "static, frozen, overexposed, cartoon, 3d render")
dtype = torch.float16 if torch.cuda.get_device_capability()[0] < 8 else torch.bfloat16
print("GPU", torch.cuda.get_device_name(0), dtype, flush=True)
vae = AutoencoderKLWan.from_pretrained(MODEL, subfolder="vae", torch_dtype=torch.float32)
pipe = WanImageToVideoPipeline.from_pretrained(MODEL, vae=vae, torch_dtype=dtype)
pipe.enable_model_cpu_offload()
pipe.vae.enable_tiling()
POST = {}


def post_models():
    """업스케일(Real-ESRGAN x4plus, BSD-3) + 얼굴 복원(GFPGAN v1.4, Apache-2.0). 실패하면 후처리 없이 진행."""
    if POST:
        return POST
    try:
        import urllib.request
        from spandrel import ModelLoader
        for name, url in (("esr", "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"),
                          ("gfp", "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth")):
            f = f"/kaggle/working/{name}.pth"
            if not os.path.exists(f):
                urllib.request.urlretrieve(url, f)
            POST[name] = ModelLoader().load_from_file(f).cuda().eval()
        for name in ("esr", "gfp"):
            os.remove(f"/kaggle/working/{name}.pth")
    except Exception as e:  # noqa: BLE001
        print("[post] 후처리 모델 로드 실패:", e, flush=True)
    return POST


def enhance(frames, out_w=1080, out_h=1920):
    """프레임마다 4배 업스케일 → 1080x1920, 얼굴은 GFPGAN으로 복원해 50% 섞기."""
    import cv2
    import numpy as np
    m = post_models()
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    out = []
    for fr in frames:
        a = np.asarray(fr).astype("float32")
        a = a / 255.0 if a.max() > 1.5 else a
        if "esr" in m:
            with torch.no_grad():
                t = torch.from_numpy(a).permute(2, 0, 1)[None].cuda()
                a = m["esr"](t)[0].permute(1, 2, 0).clamp(0, 1).float().cpu().numpy()
        img = (a * 255).astype("uint8")
        img = cv2.resize(img, (out_w, out_h), interpolation=cv2.INTER_AREA)
        if "gfp" in m:
            g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            for (x, y, w, h) in casc.detectMultiScale(g, 1.1, 6, minSize=(60, 60)):
                cx, cy, sz = x + w // 2, y + h // 2, int(max(w, h) * 1.6)
                x0, y0 = max(0, cx - sz // 2), max(0, cy - sz // 2)
                x1, y1 = min(out_w, x0 + sz), min(out_h, y0 + sz)
                crop = cv2.resize(img[y0:y1, x0:x1], (512, 512))
                with torch.no_grad():
                    t = torch.from_numpy(crop.astype("float32") / 255.0).permute(2, 0, 1)[None].cuda()
                    r = m["gfp"](t)
                    r = (r[0] if isinstance(r, (tuple, list)) else r)[0].permute(1, 2, 0).clamp(0, 1).cpu().numpy()
                r = cv2.resize((r * 255).astype("uint8"), (x1 - x0, y1 - y0))
                mask = np.zeros((y1 - y0, x1 - x0), "float32")
                cv2.ellipse(mask, ((x1 - x0) // 2, (y1 - y0) // 2), (int((x1 - x0) * .36), int((y1 - y0) * .42)), 0, 0, 360, 1, -1)
                mask = cv2.GaussianBlur(mask, (0, 0), (x1 - x0) * .06)[..., None] * 0.5
                img[y0:y1, x0:x1] = (img[y0:y1, x0:x1] * (1 - mask) + r * mask).astype("uint8")
        out.append(img)
    return out


report = {}
for j in JOBS:
    t = time.time()
    img = Image.open(io.BytesIO(base64.b64decode(j["image_b64"]))).convert("RGB").resize((j.get("w", 480), j.get("h", 832)))
    frames = pipe(image=img, prompt=j["prompt"], negative_prompt=NEG, height=img.height, width=img.width,
                  num_frames=j.get("frames", 81), num_inference_steps=j.get("steps", 30), guidance_scale=5.0,
                  generator=torch.Generator("cpu").manual_seed(j.get("seed", 7))).frames[0]
    export_to_video(frames, f"/kaggle/working/{j['name']}-raw.mp4", fps=j.get("fps", 16))
    if j.get("post", True):
        try:
            import imageio
            imageio.mimsave(f"/kaggle/working/{j['name']}.mp4", enhance(frames), fps=j.get("fps", 16), quality=9,
                            macro_block_size=8)
        except Exception as e:  # noqa: BLE001
            print("[post] 후처리 실패:", e, flush=True)
    report[j["name"]] = round(time.time() - t, 1)
    print(j["name"], report[j["name"]], flush=True)
    json.dump(report, open("/kaggle/working/report.json", "w"))
