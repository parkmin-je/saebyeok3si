"""무료 Hugging Face Space(ZeroGPU)로 1화 컷 만들기: 배우 얼굴 사진 → 장면 스틸(Qwen-Image-Edit) → 움직이는 컷(Wan 2.2).

사용: python space_runner.py <job.json> <out_dir> [<eo_repo_dir>]
job.json: {"shots":[{"name", "ref"?: 배우사진, "refs"?: [배우사진들] (투샷), "edit"?: 장면 지시, "t2i"?: 프롬프트, "still"?: 이미 있는 스틸, "motion": 움직임 프롬프트, "dur"?: 초}]}
각 결과는 나오자마자 experiment-output 브랜치에 올린다 (eo_repo_dir 이 있으면).
모든 모델은 상업 이용 가능 라이선스(Qwen-Image/Edit Apache-2.0, FLUX.1-schnell Apache-2.0, Wan 2.2 Apache-2.0).
"""
import json, shutil, subprocess, sys, time, traceback
from pathlib import Path
from gradio_client import Client, handle_file

SPACES = {
    "edit": ["linoyts/Qwen-Image-Edit-2509-Fast", "Menyu/Qwen-Image-Edit-Fast-2509",
             "LPX55/Qwen-Image-Edit-2509-Turbo-Lightning", "akhaliq/Qwen-Image-Edit-2509", "Qwen/Qwen-Image-Edit-2509"],
    "t2i": ["Qwen/Qwen-Image", "multimodalart/Qwen-Image-Fast", "black-forest-labs/FLUX.1-schnell"],
    "i2v": ["zerogpu-aoti/wan2-2-fp8da-aoti-faster", "zerogpu-aoti/wan2-2-fp8da-aoti", "KingNish/wan2-2-fast",
            "r3gm/wan2-2-fp8da-aoti-preview"],
}
NEG_V = "blurry, distorted face, deformed hands, extra fingers, morphing, flicker, low quality, watermark, text, cartoon, anime"
W, H = 720, 1280
BAD = ("update", "reset", "example", "suggest", "rewrite", "use_", "clear", "toggle", "lambda", "load", "change")
_clients = {}


def client(space):
    if space not in _clients:
        import os
        _clients[space] = Client(space, verbose=False, token=os.environ.get("HF_TOKEN") or None)
    return _clients[space]


def find(x, exts):
    if isinstance(x, str) and x.lower().split("?")[0].endswith(exts):
        return x
    if isinstance(x, dict):
        for k in ("path", "video", "image", "url", "value"):
            if k in x:
                r = find(x[k], exts)
                if r: return r
        for v in x.values():
            r = find(v, exts)
            if r: return r
    if isinstance(x, (list, tuple)):
        for v in x:
            r = find(v, exts)
            if r: return r
    return None


def pick_endpoint(api, need_image):
    best = None
    for name, ep in api["named_endpoints"].items():
        comps = [p.get("component", "") for p in ep["parameters"]]
        has_img = any(c in ("Image", "Gallery", "Imageslider") for c in comps)
        has_txt = "Textbox" in comps
        if need_image != has_img or not has_txt:
            continue
        s = len(comps) * 0.1
        if any(k in name.lower() for k in ("infer", "generate", "run", "predict", "edit")): s += 3
        if any(k in name.lower() for k in BAD): s -= 5
        if not best or s > best[0]:
            best = (s, name, ep)
    if not best:
        raise RuntimeError("맞는 엔드포인트 없음: " + str(list(api["named_endpoints"])))
    return best[1], best[2]


def call(kind, prompt, image=None, seed=0, dur=None):
    errs = []
    for space in SPACES[kind]:
        try:
            c = client(space)
            api = c.view_api(return_format="dict", print_info=False)
            name, ep = pick_endpoint(api, image is not None)
            kw, shown = {}, {}
            for p in ep["parameters"]:
                pn = p.get("parameter_name") or p.get("label")
                lab = ((p.get("label") or "") + " " + (pn or "")).lower()
                comp = p.get("component", "")
                v = None
                imgs = image if isinstance(image, list) else [image]
                if comp == "Image":   # 이미지 칸이 하나뿐이면 여러 배우를 한 장에 나란히 붙여 넣는다
                    v = handle_file(imgs[0] if len(imgs) == 1 else side_by_side(imgs, "/tmp/pair.jpg"))
                elif comp == "Gallery":   # Qwen-Image-Edit-2509는 여러 장(최대 3) 참조 가능 → 두 주인공 투샷
                    v = [{"image": handle_file(x), "caption": None} for x in imgs]
                elif comp == "Textbox" and "neg" in lab:
                    v = NEG_V if kind == "i2v" else " "
                elif comp == "Textbox" and ("prompt" in lab or "instruction" in lab or "text" in lab):
                    v = prompt
                elif "randomize" in lab:
                    v = False
                elif "seed" in lab and comp in ("Slider", "Number"):
                    v = seed
                elif kind != "i2v" and "width" in lab and comp in ("Slider", "Number"):
                    v = W
                elif kind != "i2v" and "height" in lab and comp in ("Slider", "Number"):
                    v = H
                elif kind == "i2v" and "duration" in lab and dur:
                    v = dur
                elif "aspect" in lab and comp in ("Dropdown", "Radio"):
                    v = "9:16"
                elif "rewrite" in lab and comp == "Checkbox":
                    v = False
                if v is not None:
                    kw[pn] = v
                    shown[pn] = v if isinstance(v, (int, float, bool)) or (isinstance(v, str) and len(v) < 60) else "…"
                elif not p.get("parameter_has_default"):
                    kw[pn] = None
            print(f"  [{space}] {name} {shown}", flush=True)
            t = time.time()
            for attempt in range(3):   # 무료 GPU가 잠깐 꽉 찼을 때는 같은 곳에서 다시 기다림
                try:
                    res = c.predict(api_name=name, **kw)
                    break
                except Exception as e:
                    if "No GPU was available" not in str(e) or attempt == 2:
                        raise
                    print("  GPU 대기, 30초 뒤 다시", flush=True)
                    time.sleep(30)
            exts = (".mp4", ".webm", ".mov") if kind == "i2v" else (".png", ".jpg", ".jpeg", ".webp")
            f = find(res, exts)
            print(f"  [{space}] {time.time() - t:.0f}s → {str(f)[-80:]}", flush=True)
            if not f:
                raise RuntimeError(f"결과 파일 없음: {str(res)[:200]}")
            return f, space
        except Exception as e:
            msg = f"{space}: {type(e).__name__}: {str(e)[:300]}"
            print("  실패", msg, flush=True)
            errs.append(msg)
    raise RuntimeError(" | ".join(errs))


def side_by_side(srcs, dst):
    from PIL import Image
    ims = [Image.open(x).convert("RGB") for x in srcs]
    h = min(i.height for i in ims)
    ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    out = Image.new("RGB", (sum(i.width for i in ims), h))
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width
    out.save(dst, quality=95)
    return dst


def to_vertical(src, dst):
    """배우 사진(2:3)을 9:16 캔버스로: 흐린 배경 위에 가운데 배치. 편집 모델이 세로 장면으로 채우게."""
    from PIL import Image, ImageFilter
    im = Image.open(src).convert("RGB")
    bg = im.resize((W, H)).filter(ImageFilter.GaussianBlur(30))
    s = W / im.width
    fg = im.resize((W, int(im.height * s)))
    bg.paste(fg, (0, (H - fg.height) // 2))
    bg.save(dst, quality=95)
    return dst


def push(eo, out, msg):
    if not eo:
        return
    rid = Path(out).name
    sh = lambda *a: subprocess.run(a, cwd=eo, capture_output=True, text=True)
    dst = Path(eo) / "runs" / rid
    dst.mkdir(parents=True, exist_ok=True)
    for f in Path(out).iterdir():
        shutil.copy(f, dst / f.name)
    sh("git", "add", "runs")
    sh("git", "commit", "-qm", msg)
    for _ in range(3):
        sh("git", "pull", "-q", "--rebase", "origin", "experiment-output")
        if sh("git", "push", "-q", "origin", "HEAD:experiment-output").returncode == 0:
            break


def main(job, out, eo=None, only=None):
    spec = json.loads(Path(job).read_text())
    if only:   # 일부 컷만 다시 만들기 (예: "1,2,3")
        keep = {int(x) for x in only.split(",")}
        spec["shots"] = [s for i, s in enumerate(spec["shots"]) if i in keep]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rep = {}
    for i, s in enumerate(spec["shots"]):
        n = s["name"]
        print(f"== {n}", flush=True)
        r = rep[n] = {}
        try:
            still = s.get("still")
            if not still:
                if s.get("refs"):   # 여러 배우 한 장면 (투샷)
                    f, sp = call("edit", s["edit"], image=[str(x) for x in s["refs"]], seed=s.get("seed", 100 + i))
                elif s.get("ref"):
                    v = to_vertical(s["ref"], f"/tmp/{n}-ref.jpg")
                    f, sp = call("edit", s["edit"], image=str(v), seed=s.get("seed", 100 + i))
                else:
                    f, sp = call("t2i", s["t2i"], seed=s.get("seed", 100 + i))
                still = out / f"{n}-still{Path(f).suffix}"
                shutil.copy(f, still)
                r["still"] = f"{still.name} ({sp})"
                push(eo, out, f"still {n}")
            if s.get("motion"):
                f, sp = call("i2v", s["motion"], image=str(still), dur=s.get("dur", 3.5))
                shutil.copy(f, out / f"{n}.mp4")
                r["clip"] = f"{n}.mp4 ({sp})"
        except Exception as e:
            r["error"] = str(e)[:800]
            traceback.print_exc()
        (out / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
        push(eo, out, f"clip {n}")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
