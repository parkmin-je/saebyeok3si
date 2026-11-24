"""python -m studio <명령>

check  <대본.json>...                대본 검사 (장면·인물·효과음·별표·길이)
build  <대본.json> <작업폴더>         목소리 → 타임라인 → 소리 → 렌더 → mp4 (+720p 미리보기)
       [--fake-voice] [--no-render] [--jobs 4]
stills <대본.json> <작업폴더> [--at 1,5,9]   컷 확인용 그림 몇 장 (기본: 컷마다 가운데)
"""

import argparse
import sys
from pathlib import Path

from . import episode, render, timeline, voice


def _lines(ep):
    return [s["say"] for s in ep["shots"] if s.get("say")]


def _timeline(ep, work: Path, fake: bool) -> dict:
    if fake:
        voice.fake(ep, work, _lines(ep))
    else:
        voice.make(ep, work, _lines(ep))

    def path(ln):
        return voice.final_path(ep, work, ln, fake)

    return timeline.build(ep, lambda ln: voice.length(path(ln)), path)


def _load_checked(path) -> dict:
    ep = episode.load(path)
    errs = episode.check(ep)
    if errs:
        sys.exit(f"{path}:\n  " + "\n  ".join(errs))
    return ep


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m studio", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("episodes", nargs="+")
    b = sub.add_parser("build")
    b.add_argument("episode")
    b.add_argument("work")
    b.add_argument("--fake-voice", action="store_true")
    b.add_argument("--no-render", action="store_true")
    b.add_argument("--jobs", type=int, default=4)
    s = sub.add_parser("stills")
    s.add_argument("episode")
    s.add_argument("work")
    s.add_argument("--at", default="")
    a = ap.parse_args(argv)

    if a.cmd == "check":
        for p in a.episodes:
            ep = _load_checked(p)
            print(f"{p}: 통과 (어림 {episode.estimate(ep):.0f}초, 컷 {len(ep['shots'])}개)")
        return

    ep = _load_checked(a.episode)
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    fake = a.cmd == "stills" or a.fake_voice
    tl = _timeline(ep, work, fake)
    print(f"길이 {tl['total']:.1f}초, 컷 {len(tl['shots'])}개", flush=True)
    if a.cmd == "stills":
        mids = [(s["start"] + min(s["end"], tl["card"]["start"])) / 2 for s in tl["shots"]]
        times = [float(x) for x in a.at.split(",")] if a.at else mids
        for p in render.stills(tl, work, times):
            print(p)
        return
    audio = render.mix(tl)
    if a.no_render:
        render.write_timeline(tl, work)
        return
    render.frames(tl, work, a.jobs)
    out = work / f"{ep['id']}.mp4"
    render.encode(work, audio, out, work / f"{ep['id']}-720p.mp4")
    print("완성", out)


if __name__ == "__main__":
    main()
