"""무료 오픈소스 모델을 러너(CPU)에서 직접 돌리는 공급자. 외부 유료 API 없음.

- LocalImage: diffusers 실사 이미지 (모델은 config/pipeline.yaml providers.local.image)
- LocalDepth: Depth Anything V2 Small (Apache-2.0) 깊이 추정 → parallax 움직임에 사용
무거운 import는 처음 쓸 때만 한다 (가짜·드라이런 경로에서 torch가 필요 없게).
"""
import io
from pathlib import Path

import numpy as np


def long_embed(pipe, text: str, chunks: int | None = None):
    """CLIP 77토큰 제한을 넘는 프롬프트를 75토큰씩 나눠 인코딩하고 이어 붙인다 (뒷부분 잘림 방지)."""
    import torch
    tok, enc = pipe.tokenizer, pipe.text_encoder
    ids = tok(text, add_special_tokens=False).input_ids
    n = max(1, -(-len(ids) // 75), chunks or 0)
    outs = []
    for i in range(n):
        part = ids[i * 75:(i + 1) * 75]
        part = [tok.bos_token_id] + part + [tok.eos_token_id] * (76 - len(part))
        with torch.no_grad():
            outs.append(enc(torch.tensor([part]))[0])
    return torch.cat(outs, dim=1), n


class LocalImage:
    def __init__(self, model: str, lcm_lora: str | None = None, vae: str | None = None,
                 steps: int = 6, guidance: float = 1.5, width: int = 512, height: int = 896):
        self.model, self.lcm_lora, self.vae = model, lcm_lora, vae
        self.steps, self.guidance, self.width, self.height = steps, guidance, width, height
        self.name = f"local:{model.split('/')[-1]}"
        self._pipe = None

    def _load(self):
        if self._pipe is None:
            import torch
            from diffusers import AutoencoderKL, AutoPipelineForText2Image, LCMScheduler
            kw = {"torch_dtype": torch.float32}
            if self.vae:
                kw["vae"] = AutoencoderKL.from_pretrained(self.vae, torch_dtype=torch.float32)
            p = AutoPipelineForText2Image.from_pretrained(self.model, safety_checker=None, **kw)
            if self.lcm_lora:
                p.load_lora_weights(self.lcm_lora)
                p.fuse_lora()
            p.scheduler = LCMScheduler.from_config(p.scheduler.config)
            self._pipe = p
        return self._pipe

    def _embed(self, text: str, chunks: int | None = None):
        return long_embed(self._load(), text, chunks)

    def generate(self, prompt, negative, width, height, seed, reference_images=None):
        import torch
        pipe = self._load()
        g = torch.Generator().manual_seed(seed)
        pe, n = self._embed(prompt)
        kw = {"prompt_embeds": pe}
        if self.guidance > 1:
            ne, m = self._embed(negative or "", n)
            if m > n:
                pe, _ = self._embed(prompt, m)
                kw["prompt_embeds"] = pe
            kw["negative_prompt_embeds"] = ne
        img = pipe(generator=g, width=self.width, height=self.height, num_inference_steps=self.steps,
                   guidance_scale=self.guidance, **kw).images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), 0.0


class LocalMotion:
    """인물이 실제로 움직이는 짧은 실사 컷 (AnimateDiff-Lightning + 실사 SD1.5, CPU)."""

    def __init__(self, model: str, adapter_repo: str, adapter_file: str, vae: str | None = None,
                 steps: int = 4, frames: int = 16, width: int = 384, height: int = 672, **_):
        self.model, self.adapter_repo, self.adapter_file, self.vae = model, adapter_repo, adapter_file, vae
        self.steps, self.frames, self.width, self.height = steps, frames, width, height
        self.name = f"local:animatediff-lightning/{model.split('/')[-1]}"
        self._pipe = None

    def _load(self):
        if self._pipe is None:
            import torch
            from diffusers import AnimateDiffPipeline, AutoencoderKL, EulerDiscreteScheduler, MotionAdapter
            from huggingface_hub import hf_hub_download
            from safetensors.torch import load_file
            ad = MotionAdapter()
            ad.load_state_dict(load_file(hf_hub_download(self.adapter_repo, self.adapter_file)))
            kw = {"vae": AutoencoderKL.from_pretrained(self.vae)} if self.vae else {}
            p = AnimateDiffPipeline.from_pretrained(self.model, motion_adapter=ad, torch_dtype=torch.float32, **kw)
            p.scheduler = EulerDiscreteScheduler.from_config(p.scheduler.config, timestep_spacing="trailing",
                                                             beta_schedule="linear")
            p.enable_vae_slicing()
            self._pipe = p
        return self._pipe

    def generate(self, prompt: str, seed: int) -> list:
        """RGB uint8 프레임 리스트."""
        import torch
        pipe = self._load()
        pe, _ = long_embed(pipe, prompt)
        r = pipe(prompt_embeds=pe, num_frames=self.frames, width=self.width, height=self.height,
                 num_inference_steps=self.steps, guidance_scale=1.0,
                 generator=torch.Generator().manual_seed(seed), output_type="np")
        return [(np.clip(f, 0, 1) * 255).astype(np.uint8) for f in r.frames[0]]


class LocalDepth:
    name = "local:depth-anything-v2-small"

    def __init__(self, model: str = "depth-anything/Depth-Anything-V2-Small-hf"):
        self.model = model
        self._pipe = None

    def estimate(self, image: Path) -> np.ndarray:
        """0~255 uint8 깊이 지도 (가까울수록 밝다)."""
        from PIL import Image
        from transformers import pipeline
        if self._pipe is None:
            self._pipe = pipeline("depth-estimation", model=self.model, device=-1)
        d = self._pipe(Image.open(image).convert("RGB"))["depth"]
        return np.array(d.convert("L"))
