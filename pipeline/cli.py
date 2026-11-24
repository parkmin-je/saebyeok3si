"""rrs CLI (INTERFACES.md §7 중 produce만 우선 구현).

  python -m pipeline.cli produce --script scripts/samples/1930s-001.json            # 무료: 일러스트 + 무료 TTS
  python -m pipeline.cli produce --script ... --mode veo --quality fast             # 유료: 나노바나나 + Veo
  python -m pipeline.cli produce --script ... --fake                                # 외부 호출 없는 드라이런

종료 코드: 0 성공, 1 품질 실패, 2 공급자 실패, 3 치명, 4 예산 초과.
"""
import argparse
import datetime as dt
import secrets
import sys
from pathlib import Path

import yaml

from .core.errors import PipelineError
from .core.io import read_json, write_json
from .providers import registry
from .stages import gate_video, music, render, timeline, voice
from .stages.common import Ctx

REPO = Path(__file__).resolve().parent.parent


def produce(a) -> int:
    cfg = yaml.safe_load((REPO / "config" / "pipeline.yaml").read_text(encoding="utf-8"))
    script = read_json(a.script)
    run_id = a.run_id or f"{dt.datetime.now():%Y%m%d-%H%M}-{script['era']}-{secrets.token_hex(2)}"
    run_dir = REPO / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "script.json", script)
    ctx = Ctx(run_dir=run_dir, repo=REPO, script=script, cfg=cfg,
              providers=registry.build(cfg, a.quality, a.fake),
              budget_usd=float(cfg["budget"]["per_episode_usd"]))
    ctx.log(f"[run] {run_id} 모드={a.mode} fake={a.fake}")
    voice.run(ctx)
    timeline.run(ctx)
    tl = read_json(run_dir / "timeline.json")
    if a.mode == "veo":
        from .stages import clips, images
        images.run(ctx)
        clips.run(ctx)
        raise PipelineError("veo 모드의 클립 합성 렌더는 아직 구현 전입니다 (무료 일러스트 모드를 쓰세요)")
    music.run(ctx, tl["duration_sec"])
    fr = render.frames(ctx)
    mx = render.mix(ctx, tl)
    out = render.final(ctx, tl, fr, mx)
    render.cover(ctx, fr)
    rep = gate_video.check(out, run_dir / "qa" / "video.json")
    ctx.log(f"[gate] video passed={rep['passed']} {rep['metrics']} {rep['issues']}")
    ctx.log(f"[done] {out} (비용 ${ctx.spent_usd:.2f})")
    return 0 if rep["passed"] else 1


def daily(a) -> int:
    """하루 1편 자동 제작: 소재 선택 → 대본(Gemini 무료) → 음성 → 실사 이미지(로컬 모델) → 깊이 → 입체 움직임 → 렌더."""
    from .providers.gemini_text import GeminiText
    from .providers.local_models import LocalDepth, LocalImage, LocalMotion
    from .stages import images, motion, photo, script as script_stage

    cfg = yaml.safe_load((REPO / "config" / "pipeline.yaml").read_text(encoding="utf-8"))
    hist_path = REPO / "data" / "history.json"
    history = read_json(hist_path) if hist_path.exists() else []
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    run_id = a.run_id or f"{now:%Y%m%d}-2000s-{secrets.token_hex(2)}"
    run_dir = REPO / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    log = lambda m: (print(m, flush=True), open(run_dir / "logs.txt", "a", encoding="utf-8").write(m + "\n"))
    seed = int(now.strftime("%Y%m%d"))

    g = cfg["providers"]["gemini"]
    llm = registry.Chain("llm", [GeminiText(m) for m in g["text"]], log)
    sp = run_dir / "script.json"
    if sp.exists():
        script = read_json(sp)
        topic = (read_json(run_dir / "topic.json") if (run_dir / "topic.json").exists() else {"topic": "?"})["topic"]
    else:
        script, topic = script_stage.run(REPO, llm, history, seed, sp, log)
        write_json(run_dir / "topic.json", {"topic": topic})

    lc = cfg["providers"]["local"]
    provs = registry.build(cfg, "fast", a.fake, log)
    if not a.fake:
        provs["image"] = registry.Chain("image", [LocalImage(**lc["image"])], log)
    ctx = Ctx(run_dir=run_dir, repo=REPO, script=script, cfg=cfg, providers=provs,
              budget_usd=float(cfg["budget"]["per_episode_usd"]))
    voice.run(ctx)
    timeline.run(ctx)
    tl = read_json(run_dir / "timeline.json")
    mc = lc.get("motion") or {}
    if not a.fake and mc.get("max_scenes", 0) > 0:
        motion.run(ctx, LocalMotion(**mc), int(mc["max_scenes"]), float(mc.get("fps_in", 7)))
    images.run(ctx, photo_style=True)
    if not a.fake:
        photo.depth_maps(ctx, LocalDepth(lc["depth"]))
    photo.frames(ctx)
    music.run(ctx, tl["duration_sec"])
    fr = run_dir / "render" / "frames.mp4"
    mx = render.mix(ctx, tl)
    out = render.final(ctx, tl, fr, mx)
    render.cover(ctx, fr)
    rep = gate_video.check(out, run_dir / "qa" / "video.json")
    log(f"[gate] video passed={rep['passed']} {rep['metrics']} {rep['issues']}")
    if rep["passed"]:
        history.append({"date": now.strftime("%Y-%m-%d"), "run_id": run_id, "topic": topic,
                        "title": script["title"], "id": script["id"]})
        write_json(hist_path, history)
    return 0 if rep["passed"] else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rrs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("produce")
    p.add_argument("--script", required=True, type=Path)
    p.add_argument("--run-id")
    p.add_argument("--mode", choices=["illustrated", "veo"], default="illustrated")
    p.add_argument("--quality", choices=["fast", "max"], default="fast")
    p.add_argument("--fake", action="store_true")
    d = sub.add_parser("daily")
    d.add_argument("--run-id")
    d.add_argument("--fake", action="store_true")
    a = ap.parse_args(argv)
    try:
        return produce(a) if a.cmd == "produce" else daily(a)
    except PipelineError as e:
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr)
        return e.exit_code


if __name__ == "__main__":
    sys.exit(main())
