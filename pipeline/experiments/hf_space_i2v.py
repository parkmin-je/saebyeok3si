"""무료 Hugging Face Space(ZeroGPU)의 Wan 2.2 데모로 사진→영상 컷 만들기 (Kaggle 대기열 우회용).

사용: python hf_space_i2v.py <image> <prompt> <out_dir>
여러 Space를 차례로 시도하고, API를 읽어 이미지·프롬프트 칸을 자동으로 채운다.
"""
import json, shutil, sys, time, traceback
from pathlib import Path
from gradio_client import Client, handle_file

SPACES = [
    "zerogpu-aoti/wan2-2-fp8da-aoti-faster",
    "zerogpu-aoti/wan2-2-fp8da-aoti",
    "KingNish/wan2-2-fast",
    "r3gm/wan2-2-fp8da-aoti-preview",
    "linoyts/wan2-2-i2v-rCM",
    "Wan-AI/Wan-2.2-5B",
]
NEG = "blurry, distorted face, deformed, extra fingers, low quality, watermark, text, cartoon"


def find_video(x):
    if isinstance(x, str) and x.lower().endswith((".mp4", ".webm", ".mov")):
        return x
    if isinstance(x, dict):
        for v in x.values():
            r = find_video(v)
            if r: return r
    if isinstance(x, (list, tuple)):
        for v in x:
            r = find_video(v)
            if r: return r
    return None


def try_space(space, image, prompt, out):
    c = Client(space, verbose=False)
    api = c.view_api(return_format="dict", print_info=False)
    eps = api["named_endpoints"]
    print(f"[{space}] endpoints: {list(eps)}", flush=True)
    # 이미지 입력이 있는 엔드포인트 고르기
    best = None
    for name, ep in eps.items():
        comps = [p.get("component", "") for p in ep["parameters"]]
        if "Image" in comps:
            score = ("video" in name or "generate" in name or "predict" in name) * 2 + 1
            if not best or score > best[0]:
                best = (score, name, ep)
    if not best:
        raise RuntimeError("이미지 입력 엔드포인트 없음")
    _, name, ep = best
    kw = {}
    for p in ep["parameters"]:
        pn = p.get("parameter_name") or p.get("label")
        lab = (p.get("label") or "").lower() + " " + (pn or "").lower()
        comp = p.get("component", "")
        if comp == "Image":
            kw[pn] = handle_file(image)
        elif comp == "Textbox" and "neg" in lab:
            kw[pn] = NEG
        elif comp == "Textbox" and "prompt" in lab:
            kw[pn] = prompt
        elif "duration" in lab and p.get("parameter_has_default"):
            kw[pn] = min(max(p.get("parameter_default") or 3, 3), 5)
    print(f"[{space}] {name} args={ {k: (v if isinstance(v, (str, int, float)) else 'file') for k, v in kw.items()} }", flush=True)
    t = time.time()
    res = c.predict(api_name=name, **kw)
    v = find_video(res)
    print(f"[{space}] {time.time() - t:.0f}s result={str(res)[:300]}", flush=True)
    if not v:
        raise RuntimeError("영상 결과 없음")
    dst = Path(out) / (space.replace("/", "__") + ".mp4")
    shutil.copy(v, dst)
    return dst


def main(image, prompt, out):
    Path(out).mkdir(parents=True, exist_ok=True)
    log = {}
    for s in SPACES:
        try:
            d = try_space(s, image, prompt, out)
            log[s] = f"ok {d.name}"
            print(f"성공: {s} → {d}", flush=True)
            break  # 무료 할당량 아끼기: 하나 성공하면 끝
        except Exception as e:
            log[s] = f"fail {type(e).__name__}: {str(e)[:300]}"
            traceback.print_exc()
    Path(out, "report.json").write_text(json.dumps(log, ensure_ascii=False, indent=1))
    print(json.dumps(log, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
