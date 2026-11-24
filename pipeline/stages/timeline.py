"""S5 timeline: 실측 음성 길이로 장면 시작/끝과 자막 타이밍을 정한다 (INTERFACES.md §6)."""
from ..core.errors import QualityError
from ..core.io import read_json, write_json
from .common import Ctx, nn

name = "timeline"
LEAD_IN, GAP, TAIL, MAX_TOTAL, CAP_MAX = 0.4, 0.35, 0.6, 59.0, 14


def split_caption(text: str, limit: int = CAP_MAX) -> list[str]:
    """띄어쓰기 단위로 limit자 이하 줄로 나눈다."""
    lines, cur = [], ""
    for w in text.split():
        cand = f"{cur} {w}".strip()
        if len(cand) <= limit:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            while len(w) > limit:
                lines.append(w[:limit])
                w = w[limit:]
            cur = w
    if cur:
        lines.append(cur)
    return lines


def run(ctx: Ctx) -> None:
    s = ctx.script
    vidx = read_json(ctx.run_dir / "audio" / "voice" / "index.json")["segments"]
    by_scene: dict[int, list] = {}
    for seg in vidx:
        by_scene.setdefault(seg["no"], []).append(seg)

    need, plan = [], []
    for sc in s["scenes"]:
        segs = sorted(by_scene.get(sc["no"], []), key=lambda x: x["seq"])
        t, placed = LEAD_IN, []
        for seg in segs:
            placed.append((t, seg))
            t += seg["duration_sec"] + GAP
        voice_need = (t - GAP + TAIL) if segs else 0
        need.append(voice_need)
        plan.append([sc, placed, max(float(sc["duration_sec"]), voice_need)])

    total = sum(p[2] for p in plan)
    if total > MAX_TOTAL:  # 비례 축소하되 음성보다 짧게는 만들지 않는다
        slack = sum(p[2] - n for p, n in zip(plan, need))
        over = total - MAX_TOTAL
        if over > slack:
            raise QualityError("NARRATION_TOO_LONG", f"음성 합계가 {total:.1f}s로 {MAX_TOTAL}s를 넘습니다")
        for p, n in zip(plan, need):
            p[2] -= over * (p[2] - n) / slack if slack else 0

    scenes, start = [], 0.0
    for sc, placed, length in plan:
        caps, voice = [], []
        for t0, seg in placed:
            voice.append({"file": seg["file"], "start": round(start + t0, 3)})
            text = seg["text"]
            lines = split_caption(text, CAP_MAX - 2 if seg["speaker"] != "N" else CAP_MAX)
            # 두 줄씩 묶어 보여 주고, 글자 수 비율로 시간을 나눈다
            groups = [lines[i:i + 2] for i in range(0, len(lines), 2)]
            total_chars = sum(len("".join(gr)) for gr in groups)
            t = start + t0
            for gi, gr in enumerate(groups):
                d = seg["duration_sec"] * len("".join(gr)) / total_chars
                for li, line in enumerate(gr):
                    if seg["speaker"] != "N":
                        line = ("“" if gi == 0 and li == 0 else "") + line + \
                               ("”" if gi == len(groups) - 1 and li == len(gr) - 1 else "")
                    caps.append({"text": line, "start": round(t, 3), "end": round(t + d + 0.15, 3),
                                 "row": li, "rows": len(gr), "speaker": seg["speaker"]})
                t += d
        scenes.append({
            "no": sc["no"], "start": round(start, 3), "end": round(start + length, 3),
            "image": f"images/scene-{nn(sc['no'])}.png",
            "motion": {"type": "static"},
            "transition_in": {"type": "crossfade" if sc["no"] > 1 else "cut", "sec": 0.8 if sc["no"] > 1 else 0},
            "voice": voice, "captions": caps,
        })
        start += length
    write_json(ctx.run_dir / "timeline.json", {
        "schema_version": "1.0.0", "fps": 30, "width": 1080, "height": 1920,
        "duration_sec": round(start, 3), "scenes": scenes,
        "bgm": {"file": "audio/bgm.wav", "gain_db": -16, "duck_under_voice_db": -8},
        "sfx": [],
    })
    ctx.log(f"[timeline] 총 {start:.1f}s, 장면 " + ", ".join(f"{x['end'] - x['start']:.1f}" for x in scenes))
