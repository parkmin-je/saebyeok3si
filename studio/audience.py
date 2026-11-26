"""가상 시청자 실험: 영상을 Gemini(무료)에게 실제로 보여주고, 시청자 유형별로 언제 넘기는지 확률을 받아
1만 명으로 몬테카를로를 돌린다. 실제 조회수 예측이 아니라 '어디서 빠지는가'를 비교하는 도구다.

python -m studio.audience 영상.mp4 [--n 10000] [--out 결과.json]
"""

import argparse
import base64
import json
import random
import sys
from pathlib import Path

from .voice import _post

PANEL_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]
MARKS = [1, 3, 5, 10, 15, 20, 30, "end"]

# 한국 유튜브 쇼츠 피드에서 이 영상을 '추천받아 보게 될' 사람들 (비중 합 100)
PERSONAS = [
    ("20대 후반 신입·주니어 개발자, AI 대체 불안 있음", 9),
    ("30대 초반 대리급 직장인, 회사 공감 콘텐츠 좋아함", 12),
    ("20대 중반 취준생, 자소서·면접 스트레스", 10),
    ("30대 중반 팀장급, AI 도입 압박 받는 중", 6),
    ("20대 초반 대학생, 웃긴 짤·밈 위주로 넘겨봄", 12),
    ("10대 후반 고등학생, 쇼츠 하루 2시간", 8),
    ("40대 직장인, 출퇴근길 쇼츠", 9),
    ("20~30대 여성 직장인, 귀여운 동물 캐릭터 좋아함", 10),
    ("IT 무관 서비스직 20대, 개발 용어 모름", 8),
    ("AI 기술 덕후, AI 뉴스·툴 리뷰 위주로 봄", 6),
    ("50대 이상, 손주 영상·뉴스 쇼츠 위주", 5),
    ("웹툰·애니 좋아하는 20대, 그림체에 민감", 5),
]

PROMPT = """너는 유튜브 쇼츠 시청 행동 연구자다. 이 세로 영상(약 {dur:.0f}초)이 한국 사용자 쇼츠 피드에 추천으로 떴다고 하자.
아래 시청자 유형마다, 이 영상을 '실제로 처음부터 본다'고 상상하고 냉정하게 판단해라. 쇼츠 피드에서는 평균적으로 많은 사람이 1~2초 안에 넘긴다.
칭찬하지 말고, 진짜 사람이 엄지손가락으로 넘기는 순간을 기준으로 해라.

각 유형마다 그 유형 100명 중 해당 시점까지 '아직 보고 있는' 사람 수(0~100, 시간이 갈수록 줄어듦)를 줘라:
s1(1초), s3(3초), s5, s10, s15, s20, s30, end(끝까지).
그리고 like(좋아요 누를 사람 수/100), comment, share, rewatch(다시 볼 사람)와,
가장 많이 빠지는 순간(drop_sec)과 이유(why, 한 문장), 계속 보게 만든 요소(hook, 한 문장)를 줘라.

시청자 유형:
{personas}

JSON 배열로만 답해라: [{{"i":번호,"s1":..,"s3":..,"s5":..,"s10":..,"s15":..,"s20":..,"s30":..,"end":..,"like":..,"comment":..,"share":..,"rewatch":..,"drop_sec":..,"why":"..","hook":".."}}]
마지막에 배열 말고는 아무것도 쓰지 마라."""


def ask(model: str, video: bytes, dur: float) -> list[dict]:
    ps = "\n".join(f"{i}. {p}" for i, (p, _) in enumerate(PERSONAS))
    body = {
        "contents": [
            {
                "parts": [
                    {"inlineData": {"mimeType": "video/mp4", "data": base64.b64encode(video).decode()}},
                    {"text": PROMPT.format(dur=dur, personas=ps)},
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
    }
    d = _post(model, body)
    return json.loads(d["candidates"][0]["content"]["parts"][0]["text"])


def curve(r: dict) -> list[float]:
    """s1..end 를 0~1 의 단조 감소 생존 곡선으로."""
    out, prev = [], 1.0
    for k in ("s1", "s3", "s5", "s10", "s15", "s20", "s30", "end"):
        v = min(prev, max(0.0, float(r.get(k, 0)) / 100))
        out.append(v)
        prev = v
    return out


def simulate(panels: list[list[dict]], n: int, seed: int = 7) -> dict:
    rng = random.Random(seed)
    weights = [w for _, w in PERSONAS]
    # 유형별로 패널(모델)들의 곡선을 평균
    avg = []
    for i in range(len(PERSONAS)):
        rows = [next((r for r in p if int(r.get("i", -1)) == i), None) for p in panels]
        rows = [r for r in rows if r]
        cs = [curve(r) for r in rows]
        c = [sum(x[k] for x in cs) / len(cs) for k in range(len(MARKS))]
        extra = {k: sum(float(r.get(k, 0)) for r in rows) / len(rows) / 100 for k in ("like", "comment", "share", "rewatch")}
        avg.append((c, extra, rows))
    alive = [0] * len(MARKS)
    act = dict.fromkeys(("like", "comment", "share", "rewatch"), 0)
    per = [[0, 0] for _ in PERSONAS]
    for _ in range(n):
        i = rng.choices(range(len(PERSONAS)), weights)[0]
        c, extra, _ = avg[i]
        u = rng.random()  # 이 사람의 '참을성' — 곡선 아래면 그 시점까지 봄
        for k, v in enumerate(c):
            if u < v:
                alive[k] += 1
        per[i][0] += 1
        if u < c[-1]:
            per[i][1] += 1
        for a in act:  # extra 는 그 유형 100명당 반응 수
            if rng.random() < extra[a]:
                act[a] += 1
    return {
        "n": n,
        "alive": dict(zip([str(m) for m in MARKS], alive, strict=True)),
        "actions": act,
        "by_persona": [
            {
                "who": PERSONAS[i][0],
                "share_of_viewers": per[i][0],
                "finished": per[i][1],
                "curve": [round(x, 2) for x in avg[i][0]],
                "drop_sec": [r.get("drop_sec") for r in avg[i][2]],
                "why": [r.get("why") for r in avg[i][2]],
                "hook": [r.get("hook") for r in avg[i][2]],
            }
            for i in range(len(PERSONAS))
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--panels", type=int, default=3)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    import subprocess

    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video]).decode())
    video = Path(a.video).read_bytes()
    panels, used = [], []
    for m in PANEL_MODELS:
        if len(panels) >= a.panels:
            break
        try:
            panels.append(ask(m, video, dur))
            used.append(m)
            print(f"패널 {m}: 응답", file=sys.stderr)
        except Exception as e:  # noqa: BLE001 - 다음 모델로
            print(f"패널 {m}: 실패 {type(e).__name__}", file=sys.stderr)
    if not panels:
        sys.exit("패널 모델이 모두 막힘")
    res = simulate(panels, a.n)
    res["panels"] = used
    res["duration"] = dur
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
