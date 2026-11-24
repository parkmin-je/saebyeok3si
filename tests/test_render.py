"""장면이 실제로 그려지는지 (Playwright 가 있을 때만)."""

import shutil
import subprocess

import pytest

from studio import ROOT, WEB, episode, render, timeline, voice


def _playwright():
    if not shutil.which("node"):
        return False
    r = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True, cwd=WEB, check=False)
    return r.returncode == 0


@pytest.mark.skipif(not _playwright(), reason="node playwright 없음")
def test_smoke_episode_renders_nonblank_stills(tmp_path):
    from PIL import Image

    ep = episode.load(ROOT / "examples/smoke.json")
    lines = [s["say"] for s in ep["shots"] if s.get("say")]
    voice.fake(ep, tmp_path, lines)

    def path(ln):
        return voice.final_path(ep, tmp_path, ln, fake=True)

    tl = timeline.build(ep, lambda ln: voice.length(path(ln)), path)
    times = [(s["start"] + min(s["end"], tl["card"]["start"])) / 2 for s in tl["shots"]] + [tl["card"]["start"] + 1]
    files = render.stills(tl, tmp_path, times)
    assert len(files) == len(times)
    for f in files:
        im = Image.open(f).convert("L").resize((54, 96))
        lo, hi = im.getextrema()
        assert hi - lo > 60, f"{f.name} 가 거의 한 색"
