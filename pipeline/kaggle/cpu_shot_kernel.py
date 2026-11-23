"""Kaggle 무료 CPU 커널(템플릿, GPU 없이): 한 컷 = 배우 얼굴 스틸 → 짧은 영상. 느리지만 완전 무료.

1) 스틸: RealVisXL V5.0 (SDXL 실사) + IP-Adapter Plus Face SDXL로 배우 얼굴 유지 (참조 없으면 엑스트라 컷)
   이미 만든 스틸(still_b64)이 있으면 건너뜀
2) 영상: FastWan2.2-TI2V-5B (Wan 2.2 TI2V-5B를 3스텝으로 증류, Apache-2.0) → 실패하면 Wan2.2-TI2V-5B 원본 10스텝
메모리 30GB 안에서 돌게: 프롬프트를 먼저 인코딩하고 텍스트 인코더를 지운 뒤 영상 모델을 돌린다.
JOBS: [{name, prompt(스틸), motion(영상), ref_b64|null, still_b64|null, seed, frames}]
결과: /kaggle/working/<name>-still.png, <name>.mp4, report.json
"""
import base64, gc, io, json, os, subprocess, sys, time, traceback

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.1", "transformers>=4.49", "accelerate",
                "ftfy", "imageio", "imageio-ffmpeg", "sentencepiece"], check=True)
import torch  # noqa: E402
from PIL import Image  # noqa: E402

torch.set_num_threads(os.cpu_count() or 4)
JOBS = json.loads(base64.b64decode("__JOBS__").decode())
OUT = "/kaggle/working"
REPORT = {}
NEG_I = ("(worst quality, low quality:1.4), deformed face, asymmetric eyes, blurry face, extra fingers, mutated hands, "
         "bad anatomy, cartoon, anime, 3d render, plastic skin, text, watermark, logo, nsfw")
NEG_V = ("blurry, low quality, deformed face, extra limbs, distorted hands, text, watermark, static, frozen, "
         "overexposed, cartoon")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def save_report():
    json.dump(REPORT, open(f"{OUT}/report.json", "w"), ensure_ascii=False, indent=1)


def make_still(j):
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLPipeline
    from transformers import CLIPVisionModelWithProjection
    enc = CLIPVisionModelWithProjection.from_pretrained("h94/IP-Adapter", subfolder="models/image_encoder",
                                                        torch_dtype=torch.float32)
    pipe = StableDiffusionXLPipeline.from_pretrained("SG161222/RealVisXL_V5.0", image_encoder=enc,
                                                     torch_dtype=torch.float32)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                         weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors")
    ref = Image.open(io.BytesIO(base64.b64decode(j["ref_b64"]))).convert("RGB") if j.get("ref_b64") else None
    pipe.set_ip_adapter_scale(0.6 if ref else 0.0)
    t = time.time()
    img = pipe(prompt=j["prompt"], negative_prompt=NEG_I, ip_adapter_image=ref or Image.new("RGB", (224, 224), 128),
               width=j.get("w", 704), height=j.get("h", 1232), num_inference_steps=j.get("steps", 26),
               guidance_scale=5.0, generator=torch.Generator("cpu").manual_seed(j.get("seed", 100))).images[0]
    log("스틸", j["name"], round(time.time() - t), "초")
    del pipe, enc
    gc.collect()
    return img


def make_clip(j, still):
    from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
    from diffusers.utils import export_to_video
    w, h = 480, 832
    img = still.convert("RGB").resize((w, h), Image.LANCZOS)
    for model, steps, cfg in (("FastVideo/FastWan2.2-TI2V-5B-FullAttn-Diffusers", 3, 1.0),
                              ("Wan-AI/Wan2.2-TI2V-5B-Diffusers", 10, 4.0)):
        try:
            t = time.time()
            vae = AutoencoderKLWan.from_pretrained(model, subfolder="vae", torch_dtype=torch.float32)
            pipe = WanImageToVideoPipeline.from_pretrained(model, vae=vae, torch_dtype=torch.bfloat16)
            with torch.no_grad():
                pe, ne = pipe.encode_prompt(prompt=j["motion"], negative_prompt=NEG_V,
                                            do_classifier_free_guidance=cfg > 1, device="cpu")
            pipe.text_encoder = None   # 메모리 확보 (약 11GB)
            gc.collect()
            log("영상 시작", model, steps, "스텝")
            frames = pipe(image=img, prompt_embeds=pe, negative_prompt_embeds=ne if cfg > 1 else None,
                          height=h, width=w, num_frames=j.get("frames", 49), num_inference_steps=steps,
                          guidance_scale=cfg, generator=torch.Generator("cpu").manual_seed(j.get("seed", 7)),
                          callback_on_step_end=lambda p, i, ts, kw: (log("  스텝", i + 1), kw)[1]).frames[0]
            export_to_video(frames, f"{OUT}/{j['name']}.mp4", fps=24)
            log("영상 끝", j["name"], round(time.time() - t), "초")
            del pipe, vae
            gc.collect()
            return model
        except Exception as e:  # noqa: BLE001
            log("영상 실패", model, type(e).__name__, str(e)[:300])
            traceback.print_exc()
            gc.collect()
    raise RuntimeError("영상 모델 모두 실패")


for j in JOBS:
    r = REPORT[j["name"]] = {}
    try:
        if j.get("still_b64"):
            still = Image.open(io.BytesIO(base64.b64decode(j["still_b64"]))).convert("RGB")
        else:
            still = make_still(j)
            still.save(f"{OUT}/{j['name']}-still.png")
            r["still"] = "ok"
            save_report()
        if j.get("motion"):
            r["clip"] = make_clip(j, still)
    except Exception as e:  # noqa: BLE001
        r["error"] = f"{type(e).__name__}: {str(e)[:500]}"
        traceback.print_exc()
    save_report()
