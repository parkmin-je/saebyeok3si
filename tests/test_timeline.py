from pipeline.stages.timeline import split_caption
from pipeline.stages.voice import pick_voice

VOICES = {"female_old": "Gacrux", "female_mid": "Vindemiatrix", "female": "Leda", "male_old": "Charon",
          "male_mid": "Charon", "male": "Achird", "speed_old": 0.92}


def test_split_caption_respects_limit():
    lines = split_caption("그해 겨울, 그가 만주로 떠난다는 소문이 돌았다. 마지막 날, 그는 오지 않았다.")
    assert all(len(x) <= 14 for x in lines)
    assert " ".join(lines) == "그해 겨울, 그가 만주로 떠난다는 소문이 돌았다. 마지막 날, 그는 오지 않았다."


def test_split_caption_breaks_long_word():
    assert all(len(x) <= 14 for x in split_caption("가" * 30))


def test_pick_voice_by_description():
    assert pick_voice("70대 여성, 낮고 차분한 목소리", VOICES).voice_id == "Gacrux"
    assert pick_voice("70대 여성, 낮고 차분한 목소리", VOICES).speed == 0.92
    assert pick_voice("맑은 10대 여성", VOICES).voice_id == "Leda"
    assert pick_voice("정중한 30대 남성", VOICES).voice_id == "Charon"
    assert pick_voice("수줍은 20대 남성", VOICES).voice_id == "Achird"
