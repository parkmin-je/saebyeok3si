"""무료 그림 생성 (GitHub Actions 에서 실행). 샌드박스는 외부 그림 서비스가 막혀 있어서 공개 저장소 러너가 대신 뽑는다.

python tools/gen_images.py series/horror/images/ep001.json assets/gen/horror/ep001
목록 = {"style": 공통 꼬리말, "w": 너비, "h": 높이, "items": [{"name", "prompt", "seeds": [..]}]}
키 없이 쓰는 무료 서비스만 쓴다. 한 장 실패해도 나머지는 계속 뽑고, 결과를 log.txt 에 남긴다.
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "shorts-studio/1.0"}


def pollinations(prompt, w, h, seed):
    q = urllib.parse.urlencode({"width": w, "height": h, "seed": seed, "model": "flux", "nologo": "true", "enhance": "false"})
    return f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?{q}"


def hf_flux(prompt, w, h, seed):
    """Hugging Face 공개 Space (FLUX.1-schnell). 로그인 없이 하루 몇 장 무료. 품질·해상도가 가장 좋다."""
    try:
        from gradio_client import Client

        c = hf_flux.client = getattr(hf_flux, "client", None) or Client("black-forest-labs/FLUX.1-schnell")
        r = c.predict(prompt=prompt, seed=seed, randomize_seed=False, width=w, height=h, num_inference_steps=4, api_name="/infer")
        path = r[0] if isinstance(r, (list, tuple)) else r
        return Path(path).read_bytes(), ""
    except Exception as e:  # noqa: BLE001
        return None, "hf " + repr(e)[:300]


def fetch(url, tries=4):
    err = ""
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                data = r.read()
                if r.headers.get("Content-Type", "").startswith("image/") and len(data) > 20000:
                    return data, ""
                err = f"not image: {r.headers.get('Content-Type')} {data[:200]!r}"
        except Exception as e:  # noqa: BLE001 - 무엇이든 기록하고 다시 시도
            err = repr(e)[:300]
        time.sleep(70)  # 로그인 없는 사용자는 분당 한 장 정도만 허용 (402)
    return None, err


def main(spec, out):
    s = json.loads(Path(spec).read_text())
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    log = []
    for it in s["items"]:
        for seed in it.get("seeds", [1]):
            f = out / f"{it['name']}-{seed}.jpg"
            if f.exists():
                continue
            prompt = f"{it['prompt']}, {s['style']}"
            data, err = hf_flux(prompt, s["w"], s["h"], seed)
            how = "hf"
            if not data:
                time.sleep(65)
                data, err2 = fetch(pollinations(prompt, s["w"], s["h"], seed))
                how, err = "pollinations", f"{err} / {err2}"
            if data:
                f.write_bytes(data)
                log.append(f"ok {f.name} {how} {len(data)}")
            else:
                log.append(f"FAIL {f.name} {err}")
            print(log[-1], flush=True)
    (out / "log.txt").write_text("\n".join(log) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:3])
