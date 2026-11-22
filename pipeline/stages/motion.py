"""움직임 컷: 장면마다 인물이 실제로 움직이는 짧은 실사 영상(AnimateDiff-Lightning)을 만든다.

- render/motion/scene-NN.mp4 : 1080x1920, 30fps로 보간·업스케일한 움직임 컷
- images/scene-NN.png        : 컷의 마지막 프레임 → 이후 깊이·카메라 움직임이 이 장면에서 이어진다
  (images 단계는 이미 있는 장면 사진을 건너뛰므로, 이 단계를 images보다 먼저 돌린다)
"""
import subprocess

import cv2

from .common import Ctx, fill, keys_in, nn, seed_for

STYLE = ("RAW photo, candid movie still, Korea, early 2000s, nostalgic film photo, Kodak Portra 400, "
         "soft natural light, film grain, natural skin")


def pick(script: dict, max_scenes: int) -> list[int]:
    """인물이 나오는 장면을 먼저, 그다음 나머지를 원래 순서대로."""
    sc = script["scenes"]
    people = [s["no"] for s in sc if keys_in(s["image_prompt"])]
    rest = [s["no"] for s in sc if s["no"] not in people]
    chosen = set((people + rest)[:max_scenes])
    return [s["no"] for s in sc if s["no"] in chosen]


def write_clip(frames: list, out, fps_in: float) -> None:
    h, w = frames[0].shape[:2]
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                          "-r", str(fps_in), "-i", "-", "-vf",
                          "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,"
                          "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(tmp)],
                         stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"움직임 컷 인코딩 실패: {out}")
    tmp.replace(out)


def run(ctx: Ctx, provider, max_scenes: int, fps_in: float = 7.0) -> None:
    s = ctx.script
    by_no = {x["no"]: x for x in s["scenes"]}
    for no in pick(s, max_scenes):
        clip = ctx.run_dir / "render" / "motion" / f"scene-{nn(no)}.mp4"
        still = ctx.run_dir / "images" / f"scene-{nn(no)}.png"
        if clip.exists() and still.exists():
            continue
        sc = by_no[no]
        prompt = f"{fill(sc['image_prompt'], s)}, {sc.get('motion_prompt', '')}, {STYLE}"
        frames = provider.generate(prompt, seed_for(s["id"], no, "motion"))
        write_clip(frames, clip, fps_in)
        still.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(still), cv2.cvtColor(frames[-1], cv2.COLOR_RGB2BGR))
        ctx.log(f"[motion] 장면 {no} 움직임 컷 {len(frames)}프레임")
