from studio import timeline
from studio.timeline import CARD, GAP, chunks, plain


def test_chunks_keep_text_and_balance_emphasis():
    text = "오늘부터 우리 팀 *새 식구* 다. 잠도 안 자고 월급도 안 받는 *AI대리 입니다*"
    cs = chunks(text)
    assert plain(" ".join(cs)).split() == plain(text).split()
    assert all(c.count("*") % 2 == 0 for c in cs)
    assert all(len(plain(c)) <= 14 for c in cs)


def test_chunks_break_after_sentence_end():
    # 짧은 감탄(5글자 미만)은 다음 말과 붙고, 충분히 길면 문장 끝에서 끊는다
    assert chunks("네! 알겠습니다 팀장님") == ["네! 알겠습니다", "팀장님"]
    assert chunks("잠깐만요! 고객 이름이 전부 홍길동으로 바뀌는데요?") == ["잠깐만요!", "고객 이름이 전부", "홍길동으로", "바뀌는데요?"]


EP = {
    "names": {"kong": "콩사원", "cat": "냥팀장"},
    "card": {"q": "끝 질문", "s": "부제"},
    "badge": "콩사원 생존 D+3",
    "shots": [
        {"scene": "studio", "say": {"who": "kong", "text": "속으로 *울고* 있음", "inner": True}},
        {"scene": "studio", "hold": 1.0},
        {"scene": "studio", "say": {"who": "cat", "text": "AI한테 물어봤어?"}, "soft": True},
    ],
}


def test_build_uses_voice_lengths_and_places_card():
    tl = timeline.build(EP, lambda ln: 2.0, lambda ln: f"/v/{ln['who']}.wav")
    s = tl["shots"]
    assert s[0]["start"] == 0 and s[1]["start"] == round(2.0 + GAP, 3)
    assert s[2]["start"] == round(2.0 + GAP + 1.0, 3)
    end = round(2 * (2.0 + GAP) + 1.0, 3)
    assert tl["card"]["start"] == end and tl["total"] == round(end + CARD, 3)
    assert s[-1]["end"] == tl["total"]  # 마지막 장면이 카드 밑에 깔림
    assert tl["soft_from"] == s[2]["start"]
    assert tl["badge"] == "콩사원 생존 D+3"


def test_inner_voice_captions_are_marked():
    tl = timeline.build(EP, lambda ln: 2.0, lambda ln: "x.wav")
    kong = [c for c in tl["caps"] if c["who"] == "kong"]
    assert kong and all(c["inner"] and c["name"] == "콩사원 속마음" for c in kong)
    assert sum("wav" in c for c in tl["caps"]) == 2  # 줄마다 첫 덩어리에만 소리
    assert all(c["start"] < c["end"] for c in tl["caps"])


def test_chunks_do_not_split_short_emphasis():
    cs = chunks("오늘부터 우리 팀 *새 식구*다!")
    assert any("*새 식구*다!" in c for c in cs)
