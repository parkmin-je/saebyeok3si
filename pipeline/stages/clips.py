"""S3b clips: 장면 이미지를 Veo로 움직이는 클립으로 만든다 (ARCHITECTURE.md §10 확장)."""
from ..core.io import atomic_write, write_json
from .common import Ctx, fill, nn, seed_for

name = "clips"


def run(ctx: Ctx) -> None:
    s = ctx.script
    clip_sec = int(ctx.cfg["video"]["clip_sec"])
    out = ctx.run_dir / "clips"
    index = []
    for sc in s["scenes"]:
        p = out / f"scene-{nn(sc['no'])}.mp4"
        if not p.exists():
            prompt = (f"{sc['motion_prompt']}. {fill(sc['image_prompt'], s)}. {s['style']['visual']}. "
                      "Subtle, natural, slow movement; gentle breathing and blinking; cinematic camera. "
                      "Characters do not talk; no lip movement, no speech, no music, no text, no subtitles. "
                      f"Ambient sound only{': ' + sc['sfx'] if sc.get('sfx') else ''}.")
            (data, cost), prov = ctx.providers["video"].call(
                "animate", ctx.run_dir / "images" / f"scene-{nn(sc['no'])}.png", prompt,
                s["style"]["negative"] + ", talking, speech, music, subtitles", clip_sec,
                seed_for(s["id"], sc["no"], "clip"))
            atomic_write(p, data)
            ctx.charge(cost, f"장면 {sc['no']} 클립 {clip_sec}s ({prov})")
        index.append({"no": sc["no"], "file": f"clips/{p.name}"})
    write_json(out / "index.json", {"schema_version": "1.0.0", "clips": index})
