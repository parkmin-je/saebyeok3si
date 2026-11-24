"""G3 video gate: 플랫폼 규격·길이·음량 검사 (INTERFACES.md §4)."""
import re
import subprocess
from pathlib import Path

from ..core import media
from ..core.io import write_json


def check(video: Path, qa_path: Path) -> dict:
    issues = []
    info = media.probe(video)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    fps = eval(v["r_frame_rate"])  # "30/1"
    if (v["width"], v["height"]) != (1080, 1920) or v["codec_name"] != "h264" or round(fps) != 30 \
            or not a or a["codec_name"] != "aac":
        issues.append(("FORMAT_INVALID", f"{v['width']}x{v['height']} {v['codec_name']} {fps}fps "
                                         f"{a and a['codec_name']}"))
    if not 45 <= dur <= 59.5:
        issues.append(("DURATION_OUT_OF_RANGE", f"{dur:.1f}s"))
    p = subprocess.run(["ffmpeg", "-nostats", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", p)[-1])
    peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", p)[-1])
    if abs(lufs + 14) > 1 or peak > -1:
        issues.append(("LOUDNESS_OUT_OF_RANGE", f"{lufs} LUFS, peak {peak} dBTP"))
    size_mb = video.stat().st_size / 1e6
    if size_mb > 100:
        issues.append(("FILE_TOO_LARGE", f"{size_mb:.1f}MB"))
    report = {"schema_version": "1.0.0", "passed": not issues,
              "metrics": {"duration_sec": round(dur, 2), "lufs": lufs, "true_peak_dbtp": peak,
                          "size_mb": round(size_mb, 1)},
              "issues": [{"code": c, "message": m, "severity": "error"} for c, m in issues]}
    write_json(qa_path, report)
    return report
