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


def main(jobs_path, out_dir):
    cred = json.loads(os.environ["KAGGLE_JSON"])
    kdir = Path.home() / ".kaggle"
    kdir.mkdir(exist_ok=True)
    (kdir / "kaggle.json").write_text(json.dumps(cred))
    os.chmod(kdir / "kaggle.json", 0o600)
    user = cred["username"]
    jobs = json.loads(Path(jobs_path).read_text())
    for j in jobs:
        j["image_b64"] = base64.b64encode(Path(j.pop("image")).read_bytes()).decode()
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
