"""대본 읽기·검사. 채널 설정(series/<채널>/channel.json)의 캐릭터·목소리·D+ 도장을 대본에 채워 넣는다.

대본 모양 (series/kongsawon/epNNN.json):
{
  "id": "ep001", "series": "kongsawon", "day": 1, "mood": "bright",
  "hook": "신입 자리,|*아직* 있을까?",
  "shots": [{"scene": "studio", "o": {...}, "cam": [x, y, w], "cam2": [...], "sfx": [["ding", 0.2]],
             "say": {"who": "kong", "text": "*강조*는 별표", "how": "감정 지시", "inner": true}}],
  "tip": "AI 결과물, 배포 전에 직접 확인하기", "tip_no": 1, "end_q": "당신 팀에도 AI대리 들어왔나요?"
}
card 를 직접 주면 tip/end_q 대신 그걸 쓴다.
"""

import json
import re
from pathlib import Path

from . import ROOT, WEB
from .music import MOODS, SFX
from .timeline import CARD, GAP, HOLD, plain

CPS = 6.5  # 한국어 대사 초당 글자 수 (길이 어림)
DIRECT = "한국 회사 시트콤의 한 장면입니다. 짧고 생생하게, 웃기게 연기하세요."


def scenes() -> set[str]:
    """studio/web/*.js 에 정의된 장면 이름 (A.이름 = {...})."""
    names = set()
    for f in WEB.glob("*.js"):
        names |= set(re.findall(r"^A\.(\w+)\s*=\s*\{", f.read_text(), re.M))
    return names


def channel(name: str) -> dict:
    return json.loads((ROOT / "series" / name / "channel.json").read_text())


def load(path) -> dict:
    """대본 파일 → 렌더에 바로 쓸 수 있게 채운 dict."""
    ep = json.loads(Path(path).read_text())
    return prepare(ep)


def prepare(ep: dict) -> dict:
    ep = json.loads(json.dumps(ep))  # 원본을 건드리지 않게 깊은 복사
    ch = channel(ep["series"]) if ep.get("series") else {"cast": {}, "channel": {}, "format": {}}
    cast = ch["cast"]
    ep.setdefault("brand", ch["channel"].get("name", ""))
    ep.setdefault("names", {k: c["name"] for k, c in cast.items()})
    ep.setdefault("gvoices", {k: c["voice"] for k, c in cast.items()})
    ep.setdefault("gcast", {k: f"{c['name']} ({c['animal']}, {c['role']}). {c['persona']}" for k, c in cast.items()})
    ep.setdefault("gdirect", DIRECT)
    ep.setdefault("fx", {k: c["fx"] for k, c in cast.items() if c.get("fx", 1.0) != 1.0})
    ep.setdefault("mood", "bright")
    if ep.get("day") and ch["format"].get("badge"):
        ep.setdefault("badge", ch["format"]["badge"].format(day=ep["day"]))
    if "card" not in ep and ep.get("tip"):
        ep["card"] = {"q": f"살아남는 방법 #{ep.get('tip_no', 1)}|*{ep['tip']}*", "s": ep.get("end_q", "")}
    for s in ep["shots"]:
        ln = s.get("say")
        if ln and ln.get("inner") and ln["who"] in cast and cast[ln["who"]].get("inner_voice_how"):
            ln["how"] = ", ".join(x for x in (cast[ln["who"]]["inner_voice_how"], ln.get("how")) if x)
    return ep


def estimate(ep: dict) -> float:
    """목소리 없이 어림한 길이 (초)."""
    t = 0.0
    for s in ep["shots"]:
        if s.get("say"):
            t += len(plain(s["say"]["text"]).replace(" ", "")) / CPS + GAP + s.get("after", 0)
        else:
            t += s.get("hold", HOLD)
    return t + CARD


def check(ep: dict) -> list[str]:
    """문제 목록 (비어 있으면 통과). prepare 를 거친 대본을 넣는다."""
    errs = []
    known = scenes()
    if not ep.get("shots"):
        return ["shots 가 비어 있음"]
    if "card" not in ep:
        errs.append("끝 카드가 없음 (card, 또는 tip+end_q)")
    if ep.get("mood") not in MOODS:
        errs.append(f"모르는 mood: {ep.get('mood')} (가능: {', '.join(MOODS)})")
    for i, s in enumerate(ep["shots"], 1):
        if not s.get("scene") and not s.get("img"):
            errs.append(f"{i}번 컷: scene 이 없음")
        elif s.get("scene") and s["scene"] not in known:
            errs.append(f"{i}번 컷: 모르는 장면 {s['scene']}")
        for ev in s.get("sfx", []):
            if ev[0] not in SFX:
                errs.append(f"{i}번 컷: 모르는 효과음 {ev[0]}")
        ln = s.get("say")
        if ln:
            if not ln.get("text", "").strip():
                errs.append(f"{i}번 컷: 대사가 비어 있음")
            elif ln["text"].count("*") % 2:
                errs.append(f"{i}번 컷: 강조 별표(*)가 짝이 안 맞음")
            if ln.get("who") not in ep["gvoices"]:
                errs.append(f"{i}번 컷: 목소리가 없는 인물 {ln.get('who')}")
    limit = channel(ep["series"])["format"].get("max_seconds") if ep.get("series") else None
    if limit and estimate(ep) > limit + 8:
        errs.append(f"너무 김: 어림 {estimate(ep):.0f}초 (목표 {limit}초)")
    return errs
