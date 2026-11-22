"""실험: 무료 CPU 러너에서 '인물이 실제로 움직이는' 짧은 실사 컷을 만들 수 있는지 확인.

- 베이스: SG161222/Realistic_Vision_V5.1_noVAE (CreativeML OpenRAIL-M)
- 움직임: ByteDance/AnimateDiff-Lightning 4step (CreativeML OpenRAIL-M), 4스텝, guidance 1.0
- 16프레임(8fps=2초) → ffmpeg minterpolate로 24fps 보간
결과: out/<res>/<key>.mp4 + out/report.json
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from diffusers import AnimateDiffPipeline, AutoencoderKL, EulerDiscreteScheduler, MotionAdapter
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

STYLE = "RAW photo, Korea, early 2000s, nostalgic film photo, Kodak Portra 400, soft grain, natural skin, candid"
PROMPTS = [
    ("run", "Korean kids in school uniforms running and laughing across an apartment playground at golden hour, hair moving, " + STYLE),
    ("hair", "a Korean high school girl in a navy uniform turning her head and smiling, long hair blowing in the wind, cherry blossoms falling, " + STYLE),
    ("swing", "a Korean schoolboy swinging high on a playground swing at sunset, legs kicking, " + STYLE),
]
RES = {"s": (384, 672), "m": (448, 784)}


def save_mp4(frames, out: Path, fps_in=8):
    out.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{w}x{h}", "-r", str(fps_in), "-i", "-",
                          "-vf", "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1,scale=720:-2:flags=lanczos",
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(out)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close(); p.wait()


def main(sizes):
    t0 = time.time()
    adapter = MotionAdapter()
    adapter.load_state_dict(load_file(hf_hub_download("ByteDance/AnimateDiff-Lightning",
                                                      "animatediff_lightning_4step_diffusers.safetensors")))
    vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse")
    pipe = AnimateDiffPipeline.from_pretrained("SG161222/Realistic_Vision_V5.1_noVAE", motion_adapter=adapter,
                                               vae=vae, torch_dtype=torch.float32)
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing",
                                                        beta_schedule="linear")
    pipe.enable_vae_slicing()
    report = {"load_sec": round(time.time() - t0, 1), "clips": {}}
    for s in sizes:
        w, h = RES[s]
        for key, prompt in PROMPTS:
            t = time.time()
            r = pipe(prompt=prompt, num_frames=16, width=w, height=h, num_inference_steps=4,
                     guidance_scale=1.0, generator=torch.Generator().manual_seed(7), output_type="np")
            frames = [(np.clip(f, 0, 1) * 255).astype(np.uint8) for f in r.frames[0]]
            sec = round(time.time() - t, 1)
            save_mp4(frames, Path("out") / s / f"{key}.mp4")
            report["clips"][f"{s}/{key}"] = sec
            print(s, key, sec, flush=True)
            Path("out").mkdir(exist_ok=True)
            Path("out/report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:] or ["s", "m"])
