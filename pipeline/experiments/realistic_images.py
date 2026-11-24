"""실험: GitHub Actions CPU 러너에서 무료 오픈소스 모델로 실사 이미지를 뽑을 수 있는지 확인.

모델 후보 (상업 이용 가능한 라이선스만):
- rv51: SG161222/Realistic_Vision_V5.1_noVAE (SD1.5, CreativeML OpenRAIL-M) + LCM-LoRA (4~6스텝)
- vega: segmind/Segmind-VegaRT (Apache-2.0, SDXL 증류 + LCM)
결과: out/<model>/*.png + out/report.json (장당 시간)
"""
import json
import sys
import time
from pathlib import Path

import torch
from diffusers import AutoPipelineForText2Image, LCMScheduler, AutoencoderKL

PROMPTS = [
    ("playground", "photo of Korean children playing tag on a colorful metal jungle gym in an apartment complex playground, golden hour, 2004, film photo, warm nostalgic, candid, 35mm, soft grain"),
    ("girl", "portrait photo of a 14 year old Korean girl in a navy middle school uniform with a red ribbon, long ponytail, shy smile, classroom window light, 2000s film photo, nostalgic, natural skin"),
    ("classroom", "empty Korean middle school classroom in 2008, green chalkboard, wooden desks, autumn ginkgo trees outside the window, afternoon sunlight, film photo, nostalgic"),
    ("dusk", "empty apartment complex playground at dusk in Korea, a single child on a swing lit by a phone screen, street lamp, cinematic, melancholic, film photo"),
]
NEG = "text, watermark, logo, deformed, extra fingers, blurry face, cartoon, 3d render"


def load(name):
    if name == "rv51":
        vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse", torch_dtype=torch.float32)
        p = AutoPipelineForText2Image.from_pretrained("SG161222/Realistic_Vision_V5.1_noVAE", vae=vae,
                                                      torch_dtype=torch.float32, safety_checker=None)
        p.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")
        p.fuse_lora()
        p.scheduler = LCMScheduler.from_config(p.scheduler.config)
        return p, dict(width=512, height=896, num_inference_steps=6, guidance_scale=1.5)
    if name == "vega":
        p = AutoPipelineForText2Image.from_pretrained("segmind/Segmind-VegaRT", torch_dtype=torch.float32)
        p.scheduler = LCMScheduler.from_config(p.scheduler.config)
        return p, dict(width=576, height=1024, num_inference_steps=4, guidance_scale=0)
    raise SystemExit(name)


def main(models):
    torch.set_num_threads(max(1, torch.get_num_threads()))
    report = {}
    for m in models:
        t0 = time.time()
        pipe, kw = load(m)
        load_sec = time.time() - t0
        times = []
        for key, prompt in PROMPTS:
            g = torch.Generator().manual_seed(42)
            t = time.time()
            img = pipe(prompt=prompt, negative_prompt=NEG if kw["guidance_scale"] > 1 else None, generator=g, **kw).images[0]
            times.append(round(time.time() - t, 1))
            out = Path("out") / m / f"{key}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out)
            print(m, key, times[-1], flush=True)
        report[m] = {"load_sec": round(load_sec, 1), "per_image_sec": times, "threads": torch.get_num_threads()}
        del pipe
    Path("out/report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:] or ["rv51", "vega"])
