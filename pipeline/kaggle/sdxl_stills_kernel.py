"""Kaggle 무료 GPU 커널(템플릿): 고화질 실사 컷 스틸 + 같은 배우 얼굴 유지 + 얼굴 보정.

- 모델: RealVisXL V5.0 (SDXL, 실사), IP-Adapter Plus Face SDXL (h94/IP-Adapter, Apache-2.0)로 배우 얼굴 유지
- 얼굴 보정: OpenCV로 얼굴 찾기 → 얼굴 부분만 크게 다시 그려 붙임 (주연은 배우 얼굴 참조, 엑스트라는 참조 없이)
JOBS: [{name, prompt, ref_b64|null, n, w, h, seed}] → /kaggle/working/<name>-<k>.png
"""
import base64, io, json, subprocess, sys, time

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.1", "transformers>=4.49", "accelerate",
                "opencv-python-headless"], check=True)
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLImg2ImgPipeline, StableDiffusionXLPipeline  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402
from transformers import CLIPVisionModelWithProjection  # noqa: E402

JOBS = json.loads(base64.b64decode("__JOBS__").decode())
MODEL = "SG161222/RealVisXL_V5.0"
NEG = ("(worst quality, low quality:1.4), deformed face, asymmetric eyes, cross-eyed, blurry face, extra fingers, "
       "mutated hands, bad anatomy, cartoon, anime, 3d render, plastic skin, text, watermark, logo, nsfw, cleavage")
enc = CLIPVisionModelWithProjection.from_pretrained("h94/IP-Adapter", subfolder="models/image_encoder",
                                                    torch_dtype=torch.float16)
pipe = StableDiffusionXLPipeline.from_pretrained(MODEL, image_encoder=enc, torch_dtype=torch.float16,
                                                 variant="fp16").to("cuda")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors")
pipe.enable_vae_tiling()
i2i = StableDiffusionXLImg2ImgPipeline.from_pipe(pipe)
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
blank = Image.new("RGB", (224, 224), (128, 128, 128))


def faces(img):
    g = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    return cascade.detectMultiScale(g, 1.1, 6, minSize=(40, 40))


def detail(img, prompt, ref, seed):
    """얼굴마다 크게 다시 그리기. 가장 큰 얼굴 = 주연(배우 참조), 나머지 = 엑스트라."""
    fs = sorted(faces(img), key=lambda f: -f[2] * f[3])
    out = img.copy()
    for idx, (x, y, w, h) in enumerate(fs[:6]):
        cx, cy, s = x + w / 2, y + h / 2, max(w, h) * 2.2
        box = [int(max(0, cx - s / 2)), int(max(0, cy - s / 2)), int(min(img.width, cx + s / 2)),
               int(min(img.height, cy + s / 2))]
        crop = img.crop(box).resize((1024, 1024), Image.LANCZOS)
        main = idx == 0 and ref is not None
        pipe.set_ip_adapter_scale(0.6 if main else 0.0)
        fp = ("close-up face, " + prompt) if main else "close-up face of a Korean student, natural face, " + prompt
        new = i2i(prompt=fp, negative_prompt=NEG, image=crop, ip_adapter_image=ref if main else blank,
                  strength=0.35, num_inference_steps=30, guidance_scale=5.0,
                  generator=torch.Generator("cuda").manual_seed(seed + idx)).images[0]
        new = new.resize((box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
        m = Image.new("L", new.size, 0)
        mw, mh = new.size
        m.paste(255, (int(mw * .12), int(mh * .12), int(mw * .88), int(mh * .88)))
        out.paste(new, box[:2], m.filter(ImageFilter.GaussianBlur(mw * .06)))
    return out, len(fs)


report = {}
for j in JOBS:
    ref = Image.open(io.BytesIO(base64.b64decode(j["ref_b64"]))).convert("RGB") if j.get("ref_b64") else None
    for k in range(j.get("n", 2)):
        t = time.time()
        seed = j.get("seed", 100) + k * 1000
        pipe.set_ip_adapter_scale(0.55 if ref else 0.0)
        img = pipe(prompt=j["prompt"], negative_prompt=NEG, ip_adapter_image=ref or blank,
                   width=j.get("w", 768), height=j.get("h", 1344), num_inference_steps=32, guidance_scale=5.0,
                   generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        img, nf = detail(img, j["prompt"], ref, seed)
        img.save(f"/kaggle/working/{j['name']}-{k + 1}.png")
        report[f"{j['name']}-{k + 1}"] = {"sec": round(time.time() - t, 1), "faces": int(nf)}
        print(j["name"], k + 1, report[f"{j['name']}-{k + 1}"], flush=True)
        json.dump(report, open("/kaggle/working/report-stills.json", "w"))
