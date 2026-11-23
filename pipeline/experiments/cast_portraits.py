"""연재 드라마 주인공 후보 얼굴 뽑기 (무료 CPU, Realistic Vision + LCM). out/cast/<인물>-<n>.png"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline.providers.local_models import LocalImage  # noqa: E402

STYLE = ("RAW photo, waist-up portrait, Korean high school hallway with windows in soft winter afternoon light, "
         "2000s Korean film photo, Kodak Portra 400, film grain, natural skin texture, beautiful, k-drama lead, "
         "cinematic, shallow depth of field")
NEG = "nsfw, cleavage, child, deformed, extra fingers, text, watermark, cartoon, 3d, plastic skin, heavy makeup"
CAST = {
    "seojin": "early 20s Korean actress, bright doe eyes, long straight black hair with see-through bangs, clear fair skin, navy school blazer with red ribbon tie, white shirt, gentle confident smile",
    "doyoon": "early 20s Korean actor, tall handsome, sharp jawline, messy two-block black hair, cool gaze, navy blazer worn open over white shirt, loosened tie",
    "taeo": "early 20s Korean actor, handsome, soft warm smile, light brown wavy hair, silver round glasses, neat school uniform with beige cardigan",
    "chaerin": "early 20s Korean actress, elegant beautiful, long wavy dark brown hair with black headband, confident smile, perfectly pressed navy school blazer",
}
N = {"seojin": 3, "doyoon": 3, "taeo": 1, "chaerin": 1}

img = LocalImage("SG161222/Realistic_Vision_V5.1_noVAE", "latent-consistency/lcm-lora-sdv1-5",
                 "stabilityai/sd-vae-ft-mse", steps=6, guidance=1.5, width=512, height=768)
out = Path("out/cast")
out.mkdir(parents=True, exist_ok=True)
for who, look in CAST.items():
    for i in range(N[who]):
        data, _ = img.generate(f"{look}, {STYLE}", NEG, 0, 0, 1000 + i * 37 + len(who))
        (out / f"{who}-{i + 1}.png").write_bytes(data)
        print(who, i + 1, flush=True)
