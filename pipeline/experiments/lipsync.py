"""입 모양 맞추기: MuseTalk v1.5 (코드 MIT, 모델도 상업 이용 가능)를 무료 CPU로 돌린다.

python pipeline/experiments/lipsync.py <job.json> <out_dir>
job: {"items": [{"name", "video": mp4 경로, "audio": wav 경로, "lead": 대사 앞 무음 초(0.15)}]}
- 대사 앞뒤에 무음을 붙여 컷 길이만큼 맞춘다 → 결과 컷 길이 = 원본 컷 길이, 대사는 lead초에 시작.
- DWPose(mmpose) 대신 face_alignment 68점 랜드마크를 쓴다 (lipsync.yml에서 패치).
"""
import json
import subprocess
import sys
from pathlib import Path

import yaml

MT = Path("/tmp/MuseTalk")


def sh(*a, **k):
    print("+", " ".join(map(str, a)), flush=True)
    return subprocess.run(list(map(str, a)), check=True, **k)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip())


def main(job, out):
    spec = json.loads(Path(job).read_text())
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tasks = {}
    for i, it in enumerate(spec["items"]):
        v = Path(it["video"]).resolve()
        a = Path(it["audio"]).resolve()
        n = it["name"]
        v25 = out / f"{n}-25.mp4"
        sh("ffmpeg", "-y", "-v", "error", "-i", v, "-vf", "fps=25", "-an", "-c:v", "libx264", "-crf", "14", v25)
        lead = float(it.get("lead", 0.15))
        total = max(dur(v25), lead + dur(a) + 0.2)
        a2 = out / f"{n}-pad.wav"
        sh("ffmpeg", "-y", "-v", "error", "-i", a, "-af", f"adelay={int(lead * 1000)}:all=1,apad",
           "-t", f"{total:.3f}", "-ar", "16000", "-ac", "1", a2)
        tasks[f"task_{i}"] = {"video_path": str(v25), "audio_path": str(a2), "result_name": f"{n}.mp4"}
    cfg = out / "tasks.yaml"
    cfg.write_text(yaml.safe_dump(tasks))
    sh(sys.executable, "-m", "scripts.inference", "--inference_config", cfg, "--result_dir", out / "res",
       "--unet_model_path", "models/musetalkV15/unet.pth", "--unet_config", "models/musetalkV15/musetalk.json",
       "--version", "v15", "--fps", "25", "--batch_size", "4", "--ffmpeg_path", "/usr/bin", cwd=MT)
    for f in (out / "res").rglob("*.mp4"):
        print("결과", f, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
