"""무료 오픈소스 모델을 러너(CPU)에서 직접 돌리는 공급자. 외부 유료 API 없음.

- LocalImage: diffusers 실사 이미지 (모델은 config/pipeline.yaml providers.local.image)
- LocalDepth: Depth Anything V2 Small (Apache-2.0) 깊이 추정 → parallax 움직임에 사용
무거운 import는 처음 쓸 때만 한다 (가짜·드라이런 경로에서 torch가 필요 없게).
"""
import io
from pathlib import Path

import numpy as np


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

    def generate(self, prompt, negative, width, height, seed, reference_images=None):
        import torch
        pipe = self._load()
        g = torch.Generator().manual_seed(seed)
        img = pipe(prompt=prompt, negative_prompt=negative if self.guidance > 1 else None, generator=g,
                   width=self.width, height=self.height, num_inference_steps=self.steps,
                   guidance_scale=self.guidance).images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), 0.0


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
