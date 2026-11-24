import numpy as np
import pytest

from studio import music, render, timeline, voice
from studio.synth import SR


@pytest.mark.parametrize("name", music.SFX)
def test_every_sfx_is_finite_audio(name):
    y = music.sfx(name, None, np.random.default_rng(0))
    assert len(y) > SR * 0.2 and np.isfinite(y).all() and np.abs(y).max() <= 2


@pytest.mark.parametrize("mood", list(music.MOODS))
def test_music_length_and_level(mood):
    x = music.MOODS[mood](6.0, 4.0)
    assert len(x) == 6 * SR and np.isclose(np.abs(x).max(), 1, atol=1e-6)


def test_mix_end_to_end_with_fake_voice(tmp_path):
    ep = {
        "names": {"kong": "콩사원"},
        "gvoices": {"kong": "Puck"},
        "card": {"q": "끝"},
        "shots": [
            {"scene": "studio", "say": {"who": "kong", "text": "안녕하세요 콩사원입니다"}, "sfx": [["ding", 0.1]]},
            {"scene": "studio", "hold": 1.0},
        ],
    }
    lines = [s["say"] for s in ep["shots"] if s.get("say")]
    voice.fake(ep, tmp_path, lines)

    def path(ln):
        return voice.final_path(ep, tmp_path, ln, fake=True)

    tl = timeline.build(ep, lambda ln: voice.length(path(ln)), path)
    out = render.mix(tl)
    assert len(out) == int(tl["total"] * SR)
    assert np.isfinite(out).all() and np.abs(out).max() <= 0.93
