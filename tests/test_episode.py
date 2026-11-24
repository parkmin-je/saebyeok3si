import json

import pytest

from studio import ROOT, episode


def test_channel_and_episode_plan_are_consistent():
    ch = episode.channel("kongsawon")
    plan = json.loads((ROOT / "series/kongsawon/episodes.json").read_text())["episodes"]
    assert [e["n"] for e in plan] == list(range(1, len(plan) + 1))
    assert {e["corner"] for e in plan} <= set(ch["corners"])
    kinds = set(ch["format"]["beats"][3]["kinds"]) | {"any"}
    assert {e["twist"] for e in plan} <= kinds
    for who, c in ch["cast"].items():
        assert c["voice"] and c["name"], who


def test_prepare_fills_cast_badge_and_card():
    ep = episode.load(ROOT / "examples/smoke.json")
    assert ep["badge"] == "콩사원 생존 D+1"
    assert ep["brand"] == "콩사원 AI 생존기"
    assert ep["gvoices"]["cat"] == "Algenib"
    assert ep["card"]["q"].startswith("살아남는 방법 #1")
    inner = ep["shots"][0]["say"]
    assert inner["how"].startswith("작게")  # 채널 설정의 속마음 지시가 붙음
    assert episode.check(ep) == []


def test_known_scenes_come_from_js():
    assert {"studio", "bedroom", "elev"} <= episode.scenes()


@pytest.mark.parametrize(
    "bad, msg",
    [
        ({"scene": "nope"}, "모르는 장면"),
        ({"scene": "studio", "say": {"who": "ghost", "text": "안녕"}}, "목소리가 없는 인물"),
        ({"scene": "studio", "say": {"who": "kong", "text": "*별표 하나"}}, "별표"),
        ({"scene": "studio", "sfx": [["boing", 0]]}, "모르는 효과음"),
        ({"o": {}}, "scene 이 없음"),
    ],
)
def test_check_reports_problems(bad, msg):
    ep = episode.load(ROOT / "examples/smoke.json")
    ep["shots"].append(bad)
    assert any(msg in e for e in episode.check(ep))


def test_check_flags_too_long():
    ep = episode.load(ROOT / "examples/smoke.json")
    ep["shots"] *= 12
    assert any("너무 김" in e for e in episode.check(ep))
