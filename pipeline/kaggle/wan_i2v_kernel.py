"""Kaggle 무료 GPU에서 도는 커널 본체 (템플릿). run_kaggle.py가 JOBS를 채워 넣어 push한다.

Wan 2.2 TI2V-5B (Apache-2.0): 인물 사진 한 장 + 동작 문장 → 5초 안팎 실사 영상.
결과: /kaggle/working/<name>.mp4
"""
import base64, io, json, os, subprocess, sys, time

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.1", "transformers>=4.49",
                "accelerate", "ftfy", "imageio", "imageio-ffmpeg"], check=True)
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
report = {}
for j in JOBS:
    t = time.time()
    img = Image.open(io.BytesIO(base64.b64decode(j["image_b64"]))).convert("RGB").resize((j.get("w", 480), j.get("h", 832)))
    frames = pipe(image=img, prompt=j["prompt"], negative_prompt=NEG, height=img.height, width=img.width,
                  num_frames=j.get("frames", 81), num_inference_steps=j.get("steps", 30), guidance_scale=5.0,
                  generator=torch.Generator("cpu").manual_seed(j.get("seed", 7))).frames[0]
    export_to_video(frames, f"/kaggle/working/{j['name']}.mp4", fps=j.get("fps", 16))
    report[j["name"]] = round(time.time() - t, 1)
    print(j["name"], report[j["name"]], flush=True)
    json.dump(report, open("/kaggle/working/report.json", "w"))
