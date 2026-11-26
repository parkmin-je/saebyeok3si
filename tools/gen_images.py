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


def fetch(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                data = r.read()
                if r.headers.get("Content-Type", "").startswith("image/") and len(data) > 20000:
                    return data, ""
                err = f"not image: {r.headers.get('Content-Type')} {data[:200]!r}"
        except Exception as e:  # noqa: BLE001 - 무엇이든 기록하고 다시 시도
            err = repr(e)[:300]
        time.sleep(8 * (k + 1))
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
            data, err = fetch(pollinations(f"{it['prompt']}, {s['style']}", s["w"], s["h"], seed))
            if data:
                f.write_bytes(data)
                log.append(f"ok {f.name} {len(data)}")
            else:
                log.append(f"FAIL {f.name} {err}")
            print(log[-1], flush=True)
    (out / "log.txt").write_text("\n".join(log) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:3])
