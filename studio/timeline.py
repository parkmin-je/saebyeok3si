"""대본 + 대사 길이 → 컷 타임라인·자막 덩어리 (engine.html 이 읽는 TIMELINE)."""

import re

GAP = 0.12  # 대사 사이 숨
HOLD = 1.4  # 대사 없는 컷의 기본 길이
CARD = 3.2  # 끝 카드 길이


def plain(s: str) -> str:
    """자막 강조 표시(*단어*)를 뺀 글자."""
    return s.replace("*", "")


def chunks(text: str, n: int = 11) -> list[str]:
    """자막을 2~4어절 덩어리로 나눈다. *강조*가 두 덩어리에 걸치면 양쪽을 각각 닫고 연다."""
    out, cur = [], ""
    for w in text.split():
        if cur and len(plain(cur + " " + w)) > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
        if re.search(r"[.?!]$", plain(w)) and len(plain(cur)) >= 5:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    fixed, open_ = [], False
    for c in out:
        c2 = ("*" if open_ else "") + c
        if c2.count("*") % 2:
            c2 += "*"
            if c.count("*") % 2:
                open_ = not open_
        fixed.append(c2.replace("**", ""))
    return fixed


def build(ep: dict, voice_len, voice_path) -> dict:
    """voice_len(line) → 초, voice_path(line) → wav 경로. 대사 길이로 컷 시간을 정한다."""
    shots, caps, cuts, stages = [], [], [], []
    t = 0.0
    for s in ep["shots"]:
        start = t
        ln = s.get("say")
        if ln:
            d = voice_len(ln)
            cs = chunks(ln["text"])
            w = [len(plain(c).replace(" ", "")) + 1.5 for c in cs]
            u = t + 0.05
            for k, c in enumerate(cs):
                e = u + (d - 0.1) * w[k] / sum(w)
                cap = {"who": ln["who"], "name": ep["names"].get(ln["who"], ""), "text": c, "start": round(u, 3), "end": round(e, 3)}
                if ln.get("inner"):
                    cap["inner"] = True
                    cap["name"] += " 속마음" if cap["name"] else ""
                if k == 0:
                    cap["wav"] = str(voice_path(ln))
                caps.append(cap)
                u = e
            t += d + GAP + s.get("after", 0)
        else:
            t += s.get("hold", HOLD)
        sh = {k: v for k, v in s.items() if k not in ("say", "hold", "after")}
        sh.update(start=round(start, 3), end=round(t, 3))
        shots.append(sh)
        cuts.append(start)
        if s.get("stage"):
            stages.append(start)
    shots[-1]["end"] = round(t + CARD, 3)  # 끝 카드 뒤에도 마지막 장면이 보이게
    card = {"start": round(t, 3), "end": round(t + CARD, 3), "q": ep["card"]["q"], "s": ep["card"].get("s", "")}
    t += CARD
    return {
        "brand": ep.get("brand", ""),
        "badge": ep.get("badge", ""),
        "hook": ep.get("hook", ""),
        "hookEnd": ep.get("hookEnd", 2.6),
        "shots": shots,
        "caps": caps,
        "card": card,
        "total": round(t, 3),
        "vertical": True,
        "mood": ep.get("mood", "bright"),
        "cuts": cuts,
        "stages": stages,
        "soft_from": next((s["start"] for s in shots if s.get("soft")), t),
    }
