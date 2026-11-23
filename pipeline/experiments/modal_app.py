"""Modal 무료 크레딧(월 $30) GPU로 에피소드 컷 만들기: 배우 얼굴 스틸(Qwen-Image-Edit-2509 + Lightning 8스텝) → 영상(Wan 2.2 I2V A14B + Lightx2v 가속).

GitHub Actions에서: modal run pipeline/experiments/modal_app.py --job /tmp/job.json --out out/x --eo /tmp/eo
job.json 형식은 space_runner.py와 같다 ({"shots":[{"name","ref"|"t2i"|"still","edit","motion","dur"}], "only"?}).
라이선스: Qwen-Image-Edit-2509 Apache-2.0, Wan 2.2 Apache-2.0, Lightning LoRA Apache-2.0 (모두 상업 이용 가능).
"""
import io
import json
import math
import shutil
from pathlib import Path

import modal

app = modal.App("rrs-episode")
vol = modal.Volume.from_name("rrs-hf-cache", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git")
    .pip_install("torch==2.6.0", "torchvision", "transformers>=4.51", "accelerate>=1.6", "peft>=0.15",
                 "diffusers>=0.36.0", "sentencepiece", "ftfy", "imageio", "imageio-ffmpeg", "pillow",
                 "huggingface_hub[hf_transfer]", "safetensors")
    .env({"HF_HOME": "/cache/hf", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)
W, H = 720, 1280
import os
GPU = os.environ.get("MODAL_GPU", "L40S")   # H100·A100은 카드 등록이 필요해서 무료 플랜에선 L40S(48GB)
NEG_V = ("blurry, distorted face, deformed hands, extra fingers, morphing, flicker, low quality, watermark, text, "
         "cartoon, anime, static")


@app.cls(image=image, gpu=GPU, volumes={"/cache": vol}, timeout=3600, memory=81920, scaledown_window=120)
class EditStudio:
    @modal.enter()
    def load(self):
        import torch
        from diffusers import FlowMatchEulerDiscreteScheduler, QwenImageEditPlusPipeline
        sch = FlowMatchEulerDiscreteScheduler.from_config({
            "base_image_seq_len": 256, "base_shift": math.log(3), "invert_sigmas": False, "max_image_seq_len": 8192,
            "max_shift": math.log(3), "num_train_timesteps": 1000, "shift": 1.0, "shift_terminal": None,
            "stochastic_sampling": False, "time_shift_type": "exponential", "use_beta_sigmas": False,
            "use_dynamic_shifting": True, "use_exponential_sigmas": False, "use_karras_sigmas": False})
        self.edit_pipe = QwenImageEditPlusPipeline.from_pretrained(
            "Qwen/Qwen-Image-Edit-2509", scheduler=sch, torch_dtype=torch.bfloat16)
        self.edit_pipe.load_lora_weights(
            "lightx2v/Qwen-Image-Lightning",
            weight_name="Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-8steps-V1.0-bf16.safetensors")
        self.edit_pipe.fuse_lora()
        self.edit_pipe.to("cuda")
        vol.commit()

    def _edit(self, img: bytes, prompt: str, seed: int) -> bytes:
        import torch
        from PIL import Image
        im = Image.open(io.BytesIO(img)).convert("RGB")
        out = self.edit_pipe(image=[im], prompt=prompt, negative_prompt=" ", true_cfg_scale=1.0,
                             num_inference_steps=8, height=H, width=W,
                             generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        buf = io.BytesIO()
        out.save(buf, "PNG")
        return buf.getvalue()

    @modal.method()
    def edit(self, img: bytes, prompt: str, seed: int = 0) -> bytes:
        return self._edit(img, prompt, seed)

    @modal.method()
    def t2i(self, prompt: str, seed: int = 0) -> bytes:
        # 사람 없는 컷·엑스트라 컷: 회색 캔버스를 장면 묘사대로 새로 그리게 한다
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (W, H), (128, 128, 128)).save(buf, "PNG")
        return self._edit(buf.getvalue(), "Replace the whole image with a new photo: " + prompt, seed)


@app.cls(image=image, gpu=GPU, volumes={"/cache": vol}, timeout=3600, memory=98304, scaledown_window=120)
class VideoStudio:
    @modal.enter()
    def load(self):
        import torch
        from diffusers import WanImageToVideoPipeline
        self.vid = WanImageToVideoPipeline.from_pretrained("Wan-AI/Wan2.2-I2V-A14B-Diffusers", torch_dtype=torch.bfloat16)
        lora = ("Kijai/WanVideo_comfy", "Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank128_bf16.safetensors")
        self.vid.load_lora_weights(lora[0], weight_name=lora[1], adapter_name="lx")
        self.vid.load_lora_weights(lora[0], weight_name=lora[1], adapter_name="lx2", load_into_transformer_2=True)
        self.vid.set_adapters(["lx", "lx2"], adapter_weights=[1.0, 1.0])
        self.vid.fuse_lora(adapter_names=["lx"], lora_scale=3.0, components=["transformer"])
        self.vid.fuse_lora(adapter_names=["lx2"], lora_scale=1.0, components=["transformer_2"])
        self.vid.unload_lora_weights()
        self.vid.enable_model_cpu_offload()
        vol.commit()

    @modal.method()
    def i2v(self, img: bytes, prompt: str, dur: float = 4.0, seed: int = 0) -> bytes:
        import tempfile

        import torch
        from diffusers.utils import export_to_video
        from PIL import Image
        im = Image.open(io.BytesIO(img)).convert("RGB").resize((W, H))
        frames = int(round(dur * 16)) // 4 * 4 + 1
        out = self.vid(image=im, prompt=prompt, negative_prompt=NEG_V, height=H, width=W, num_frames=min(frames, 81),
                       guidance_scale=1.0, guidance_scale_2=1.0, num_inference_steps=6,
                       generator=torch.Generator("cuda").manual_seed(seed)).frames[0]
        f = tempfile.mktemp(suffix=".mp4")
        export_to_video(out, f, fps=16)
        return Path(f).read_bytes()


@app.local_entrypoint()
def main(job: str, out: str, eo: str = ""):
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from space_runner import push, to_vertical   # 같은 형식·같은 업로드 방식
    spec = json.loads(Path(job).read_text())
    if spec.get("only"):
        keep = {int(x) for x in str(spec["only"]).split(",")}
        spec["shots"] = [s for i, s in enumerate(spec["shots"]) if i in keep]
    outp = Path(out)
    outp.mkdir(parents=True, exist_ok=True)
    ed, vs = EditStudio(), VideoStudio()
    rep = {}
    for i, s in enumerate(spec["shots"]):
        n = s["name"]
        r = rep[n] = {}
        print("==", n, flush=True)
        try:
            still = s.get("still")
            if not still:
                if s.get("ref"):
                    v = to_vertical(s["ref"], f"/tmp/{n}-ref.jpg")
                    png = ed.edit.remote(Path(v).read_bytes(), s["edit"], s.get("seed", 100 + i))
                else:
                    png = ed.t2i.remote(s["t2i"], s.get("seed", 100 + i))
                still = outp / f"{n}-still.png"
                still.write_bytes(png)
                r["still"] = still.name
                push(eo, outp, f"modal still {n}")
            if s.get("motion"):
                mp4 = vs.i2v.remote(Path(still).read_bytes(), s["motion"], float(s.get("dur", 4)), s.get("seed", 7))
                (outp / f"{n}.mp4").write_bytes(mp4)
                r["clip"] = f"{n}.mp4"
        except Exception as e:  # noqa: BLE001
            r["error"] = f"{type(e).__name__}: {str(e)[:600]}"
            print("실패", n, r["error"], flush=True)
        (outp / f"report-{n}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
        push(eo, outp, f"modal clip {n}")
    print(json.dumps(rep, ensure_ascii=False, indent=1))
