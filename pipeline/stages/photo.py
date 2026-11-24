"""실사 모드: 장면 사진(images/) + 깊이 → 장면별 parallax 클립 → 크로스페이드로 이어 붙여 frames.mp4.

render.frames()와 같은 출력(render/frames.mp4)을 내므로 이후 mix/final/cover는 일러스트 모드와 같다.
"""
import cv2

from ..core import media
from ..core.io import read_json
from .common import Ctx, nn
from .parallax import motion_for, render_scene

XF = 0.6  # 장면 전환 크로스페이드(초)


def depth_maps(ctx: Ctx, depth_provider) -> None:
    for sc in ctx.script["scenes"]:
        out = ctx.run_dir / "images" / f"depth-{nn(sc['no'])}.png"
        if out.exists():
            continue
        d = depth_provider.estimate(ctx.run_dir / "images" / f"scene-{nn(sc['no'])}.png")
        cv2.imwrite(str(out), d)
        ctx.log(f"[depth] 장면 {sc['no']}")


MXF = 0.35  # 움직임 컷 → 카메라 움직임 이음새 페이드(초)


def _motion_then_parallax(mclip, img, depth, length, motion, out) -> None:
    """인물이 움직이는 컷을 먼저 보여주고, 그 마지막 프레임에서 카메라 움직임으로 이어 장면 길이를 채운다."""
    md = media.duration(mclip)
    if length <= md:
        media.run(["ffmpeg", "-y", "-v", "error", "-i", str(mclip), "-t", f"{length:.3f}", "-r", "30",
                   "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out)])
        return
    rest = out.with_name(out.stem + "-rest.mp4")
    render_scene(img, depth, length - md + MXF, motion, rest, strength=0.8)
    media.run(["ffmpeg", "-y", "-v", "error", "-i", str(mclip), "-i", str(rest), "-filter_complex",
               f"[0:v]fps=30,settb=AVTB[a];[1:v]fps=30,settb=AVTB[b];"
               f"[a][b]xfade=transition=fade:duration={MXF}:offset={md - MXF:.3f}[v]",
               "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out)])
    rest.unlink(missing_ok=True)


def frames(ctx: Ctx) -> None:
    out = ctx.run_dir / "render" / "frames.mp4"
    if out.exists():
        return
    tl = read_json(ctx.run_dir / "timeline.json")
    by_no = {s["no"]: s for s in ctx.script["scenes"]}
    clips, lens = [], []
    (ctx.run_dir / "render" / "clips").mkdir(parents=True, exist_ok=True)
    for i, sc in enumerate(tl["scenes"]):
        length = sc["end"] - sc["start"] + (XF if i < len(tl["scenes"]) - 1 else 0)
        dp = ctx.run_dir / "images" / f"depth-{nn(sc['no'])}.png"
        depth = cv2.imread(str(dp), cv2.IMREAD_GRAYSCALE) if dp.exists() else None
        clip = ctx.run_dir / "render" / "clips" / f"scene-{nn(sc['no'])}.mp4"
        mclip = ctx.run_dir / "render" / "motion" / f"scene-{nn(sc['no'])}.mp4"
        if not clip.exists():
            img = ctx.run_dir / "images" / f"scene-{nn(sc['no'])}.png"
            mot = motion_for(by_no[sc["no"]]["motion_prompt"])
            if mclip.exists():
                _motion_then_parallax(mclip, img, depth, length, mot, clip)
            else:
                render_scene(img, depth, length, mot, clip)
        clips.append(clip)
        lens.append(length)
        ctx.log(f"[parallax] 장면 {sc['no']} {length:.1f}s")
    # xfade 체인: 각 전환은 다음 장면의 timeline 시작 시각에 맞춘다
    args, fc, prev = [], [], "[0:v]"
    for c in clips:
        args += ["-i", str(c)]
    for i in range(1, len(clips)):
        off = tl["scenes"][i]["start"]
        lab = f"[x{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={off}{lab}")
        prev = lab
    tmp = out.with_name("frames.tmp.mp4")
    media.run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", ";".join(fc) or "null",
               "-map", prev, "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
               "-pix_fmt", "yuv420p", str(tmp)])
    tmp.replace(out)
