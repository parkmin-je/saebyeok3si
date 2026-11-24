"""S3 images: 인물 기준 이미지를 먼저 만들고, 장면 이미지는 그 기준 이미지를 참조해 만든다."""
from ..core.io import atomic_write, write_json
from .common import Ctx, fill, keys_in, nn, seed_for

name = "images"


def run(ctx: Ctx, photo_style: bool = False) -> None:
    s = ctx.script
    style = s["style"]
    out = ctx.run_dir / "images"
    refs = {}
    used = {k for sc in s["scenes"] for k in keys_in(sc["image_prompt"])}
    for c in s["characters"]:
        if photo_style:  # 로컬 모델은 참조 이미지를 못 받으므로 인물 기준 이미지를 건너뛴다
            break
        if c["key"] not in used or not c["look"]:
            continue
        p = out / f"char-{c['key']}.png"
        if not p.exists():
            prompt = (f"Character reference photo, waist-up portrait, facing camera, plain backdrop: "
                      f"{c['look']}. {style['visual']}. Photorealistic, natural skin texture.")
            (data, cost), prov = ctx.providers["image"].call(
                "generate", prompt, style["negative"], 1080, 1920, seed_for(s["id"], c["key"]))
            atomic_write(p, data)
            ctx.charge(cost, f"인물 {c['key']} ({prov})")
        refs[c["key"]] = p
    index = []
    for sc in s["scenes"]:
        p = out / f"scene-{nn(sc['no'])}.png"
        if not p.exists():
            prompt = (f"{fill(sc['image_prompt'], s)}. Setting: {sc['location']}. {style['visual']}. "
                      "Cinematic film still, photorealistic, emotional, vertical 9:16 composition with the "
                      "subject in the upper two thirds, no text.")
            if photo_style:
                prompt = (f"RAW photo, {fill(sc['image_prompt'], s)}, Korea, early 2000s, "
                          "nostalgic film photo, Kodak Portra 400, soft natural light, 35mm, film grain, "
                          "highly detailed, realistic")
            (data, cost), prov = ctx.providers["image"].call(
                "generate", prompt, style["negative"], 1080, 1920, seed_for(s["id"], sc["no"]),
                [refs[k] for k in keys_in(sc["image_prompt"]) if k in refs])
            atomic_write(p, data)
            ctx.charge(cost, f"장면 {sc['no']} 이미지 ({prov})")
        index.append({"no": sc["no"], "file": f"images/{p.name}"})
    write_json(out / "index.json", {"schema_version": "1.0.0", "images": index})
