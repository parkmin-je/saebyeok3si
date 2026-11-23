"""GitHub Actions → Kaggle 무료 GPU 커널 실행 → 결과 mp4 내려받기.

사용: python pipeline/kaggle/run_kaggle.py jobs.json out_dir
jobs.json: [{"name","prompt","image": "<로컬 경로>", "frames"?, "steps"?, "seed"?, "w"?, "h"?}]
환경변수 KAGGLE_JSON (kaggle.json 내용) 필요.
"""
import base64, json, os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).parent


def sh(*a, check=True):
    print("+", " ".join(a), flush=True)
    return subprocess.run(a, check=check, capture_output=True, text=True)


def diagnose(user, work):
    """push 400 원인 찾기: 작은 커널로 GPU/인터넷 옵션을 바꿔 가며 시도."""
    import shutil
    for gpu, net in ((False, False), (True, False), (True, True)):
        d = Path(f"/tmp/diag-{gpu}-{net}")
        d.mkdir(exist_ok=True)
        (d / "main.py").write_text("print('hello')\n")
        slug = f"rrs-diag-{int(gpu)}{int(net)}"
        (d / "kernel-metadata.json").write_text(json.dumps({
            "id": f"{user}/{slug}", "title": slug, "code_file": "main.py", "language": "python",
            "kernel_type": "script", "is_private": True, "enable_gpu": gpu, "enable_internet": net}))
        r = sh("kaggle", "kernels", "push", "-p", str(d), check=False)
        print(f"[diag] gpu={gpu} internet={net} rc={r.returncode} {r.stdout.strip()} {r.stderr.strip()[-300:]}", flush=True)
    print(f"[diag] main.py 크기 {(work / 'main.py').stat().st_size} bytes", flush=True)


def main(jobs_path, out_dir):
    cred = json.loads(os.environ["KAGGLE_JSON"])
    kdir = Path.home() / ".kaggle"
    kdir.mkdir(exist_ok=True)
    (kdir / "kaggle.json").write_text(json.dumps(cred))
    os.chmod(kdir / "kaggle.json", 0o600)
    user = cred["username"]
    jobs = json.loads(Path(jobs_path).read_text())
    for j in jobs:
        # 커널 코드 크기 제한 때문에 입력 사진은 작은 JPEG로 넣는다
        from PIL import Image
        import io
        im = Image.open(j.pop("image")).convert("RGB").resize((j.get("w", 480), j.get("h", 832)))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=92)
        j["image_b64"] = base64.b64encode(buf.getvalue()).decode()
    code = (HERE / "wan_i2v_kernel.py").read_text().replace(
        "__JOBS__", base64.b64encode(json.dumps(jobs).encode()).decode())
    slug = "rrs-wan-i2v"
    work = Path("/tmp/kernel")
    work.mkdir(exist_ok=True)
    (work / "main.py").write_text(code)
    (work / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{slug}", "title": slug, "code_file": "main.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [], "kernel_sources": []}))
    r = sh("kaggle", "kernels", "push", "-p", str(work), check=False)
    print(r.stdout, r.stderr, flush=True)
    if r.returncode != 0:
        diagnose(user, work)
        raise SystemExit("kaggle push 실패")
    t0 = time.time()
    while True:
        time.sleep(60)
        st = sh("kaggle", "kernels", "status", f"{user}/{slug}", check=False).stdout.strip()
        print(f"[{int(time.time() - t0)}s] {st}", flush=True)
        if any(w in st for w in ("complete", "error", "cancel")):
            break
        if time.time() - t0 > 4 * 3600:
            raise SystemExit("4시간 초과")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    print(sh("kaggle", "kernels", "output", f"{user}/{slug}", "-p", out_dir, check=False).stdout)
    if "complete" not in st:
        raise SystemExit(f"커널 실패: {st}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
