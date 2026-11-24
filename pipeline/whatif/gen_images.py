"""만약에 쇼츠 그림: DreamShaper XL Lightning (CreativeML OpenRAIL++-M, 상업 이용 가능)을 GitHub Actions CPU에서 돌린다.
python gen_images.py shots.json <out_dir> <shard> <num_shards>
shots.json = {"style": "...", "neg": "...", "chars": {"DOG": "..."}, "shots": [{"name", "prompt", "seeds": [1, 2]}]}
프롬프트 안의 {DOG} 같은 자리는 chars 설명으로 바꿔서 인물이 매번 같은 모습으로 나오게 한다.
"""
import json
import sys
import time
from pathlib import Path

import torch
from diffusers import AutoPipelineForText2Image, DPMSolverMultistepScheduler

job = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
k, n = int(sys.argv[3]), int(sys.argv[4])
torch.set_num_threads(4)
pipe = AutoPipelineForText2Image.from_pretrained("Lykon/dreamshaper-xl-lightning", torch_dtype=torch.float32)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
for i, s in enumerate(job["shots"]):
    if i % n != k:
        continue
    p = s["prompt"]
    for key, desc in job.get("chars", {}).items():
        p = p.replace("{" + key + "}", desc)
    p = p + ", " + job["style"]
    for seed in s.get("seeds", [1]):
        t = time.time()
        im = pipe(p, negative_prompt=job.get("neg", ""), num_inference_steps=s.get("steps", 6), guidance_scale=2.0,
                  width=s.get("w", 768), height=s.get("h", 1344), generator=torch.Generator().manual_seed(seed)).images[0]
        im.save(out / f"{s['name']}-{seed}.jpg", quality=94)
        print(s["name"], seed, f"{time.time() - t:.0f}s", flush=True)
