import numpy as np

from studio import voice
from studio.voice import SR


def L(who, text="안녕하세요 반갑습니다"):
    return {"who": who, "text": text}


def test_groups_limit_speakers_and_lines():
    lines = [L("kong"), L("cat"), L("kong"), L("bot"), L("bot"), L("bot"), L("bot"), L("bot"), L("bot"), L("cat")]
    gs = voice.groups(lines)
    assert sum(len(g) for g in gs) == len(lines)
    assert [x for g in gs for x in g] == lines  # 순서 유지
    assert all(len({x["who"] for x in g}) <= 2 and len(g) <= 5 for g in gs)


def bursts(spec):
    """[(소리 초, 쉼 초), ...] → 사인파 덩어리 녹음, 덩어리 시작·끝 목록."""
    x, marks, t = [], [], 0.0
    for on, off in spec:
        tt = np.arange(int(SR * on)) / SR
        x += [np.sin(2 * np.pi * 300 * tt) * 0.5, np.zeros(int(SR * off))]
        marks.append((t, t + on))
        t += on + off
    return np.concatenate(x).astype(np.float32), marks


def test_segments_find_bursts():
    x, marks = bursts([(1.0, 0.6), (0.8, 0.6), (1.2, 0.3)])
    segs = voice.segments(x)
    assert len(segs) == 3
    for (a, b), (ma, mb) in zip(segs, marks, strict=True):
        assert abs(a - ma) < 0.05 and abs(b - mb) < 0.05


def test_assign_gives_each_line_its_burst_and_none_for_missing():
    x, marks = bursts([(1.0, 0.6), (0.8, 0.6)])
    # 줄 1은 Gemini 가 못 찾았다고 가정
    parts = voice.assign(x, {0: marks[0], 2: marks[1]}, 3)
    assert parts[1] is None
    assert abs(len(parts[0]) / SR - 1.2) < 0.1 and abs(len(parts[2]) / SR - 1.0) < 0.1


def test_trim_and_ok_len():
    x, _ = bursts([(1.5, 0)])
    padded = np.concatenate([np.zeros(SR), x, np.zeros(SR)])
    y = voice.trim(padded)
    assert 1.5 <= len(y) / SR < 1.9
    assert voice.ok_len(np.zeros(int(SR * 1.5)), "열 글자 정도의 대사")
    assert not voice.ok_len(np.zeros(SR * 10), "짧은 말")


def test_fake_voice_and_cache_key(tmp_path):
    ep = {"gvoices": {"kong": "Puck"}}
    ln = L("kong", "*강조* 는 소리에서 빠짐")
    voice.fake(ep, tmp_path, [ln])
    p = voice.path_of(ep, tmp_path, ln, fake=True)
    assert p.exists() and voice.length(p) > 0.8
    assert voice.key_of(ep, ln) == voice.key_of(ep, {**ln, "text": "강조 는 소리에서 빠짐"})
    assert voice.key_of(ep, ln) != voice.key_of(ep, {**ln, "how": "화내며"})


def test_tts_body_single_and_multi_speaker():
    ep = {"gvoices": {"kong": "Puck", "cat": "Algenib"}, "names": {"kong": "콩사원", "cat": "냥팀장"}, "gdirect": "연기"}
    one = voice.tts_body(ep, [L("kong")])["generationConfig"]["speechConfig"]
    two = voice.tts_body(ep, [L("kong"), L("cat")])["generationConfig"]["speechConfig"]
    assert one["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"] == "Puck"
    assert [s["speaker"] for s in two["multiSpeakerVoiceConfig"]["speakerVoiceConfigs"]] == ["콩사원", "냥팀장"]


def test_make_needs_key(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    try:
        voice.make({"gvoices": {"kong": "Puck"}}, tmp_path, [L("kong")])
    except voice.VoiceError as e:
        assert "GEMINI_API_KEY" in str(e)
    else:
        raise AssertionError("키 없이 통과하면 안 됨")


def test_tighten_shortens_long_pauses_only():
    x, _ = bursts([(1.0, 0.8), (1.0, 0.2), (1.0, 0)])
    y = voice.tighten(x)
    assert abs(len(x) / SR - len(y) / SR - (0.8 - 0.22)) < 0.06  # 긴 쉼 하나만 줄어듦
    assert len(voice.segments(y)) == 2 or len(voice.segments(y, 0.15)) == 3


def test_request_falls_back_when_daily_quota_ends(monkeypatch):
    import base64
    import io
    import urllib.error

    from studio import voice

    pcm = (np.ones(2400) * 1000).astype(np.int16).tobytes()
    calls = []

    def fake_post(model, body):
        calls.append(model)
        if model == "a":
            raise urllib.error.HTTPError("u", 429, "x", {}, io.BytesIO(b"GenerateRequestsPerDayPerProjectPerModel-FreeTier"))
        return {"candidates": [{"content": {"parts": [{"inlineData": {"data": base64.b64encode(pcm).decode()}}]}}]}

    monkeypatch.setattr(voice, "TTS_MODELS", ["a", "b"])
    monkeypatch.setattr(voice, "_spent", set())
    monkeypatch.setattr(voice, "_post", fake_post)
    ep = {"gvoices": {"kong": "Puck"}}
    x = voice.request(ep, [{"who": "kong", "text": "안녕"}], log=lambda *_: None)
    assert len(x) == 2400
    voice.request(ep, [{"who": "kong", "text": "안녕"}], log=lambda *_: None)
    assert calls == ["a", "b", "b"]


def test_decode_reads_wav_and_pcm():
    import base64
    import io
    import wave

    from studio import voice

    pcm = (np.arange(100) * 10).astype(np.int16).tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(voice.SR)
        w.writeframes(pcm)
    a = voice.decode({"data": base64.b64encode(buf.getvalue()).decode()})
    b = voice.decode({"data": base64.b64encode(pcm).decode()})
    assert np.allclose(a, b) and len(a) == 100


def test_speak_drops_edge_ellipsis():
    from studio.voice import speak

    assert speak("…AI대리, *이게 뭐야*?") == "AI대리, 이게 뭐야?"
    assert speak("시키는… 대로… 했는데요?") == "시키는, 대로, 했는데요?"
    assert speak("짠 건데…") == "짠 건데"


def test_tts_body_38_multi_speaker_uses_speaker_parts():
    from studio import voice

    ep = {"gvoices": {"kong": "Puck", "cat": "Algenib"}, "names": {"kong": "콩", "cat": "냥"}}
    grp = [{"who": "kong", "text": "a", "how": "x"}, {"who": "cat", "text": "b"}]
    parts = voice.tts_body(ep, grp, "gemini-3.8-flash-tts")["contents"][0]["parts"]
    assert [p["speechMetadata"]["speaker"] for p in parts] == ["콩", "냥"]
    assert len(voice.tts_body(ep, grp, "gemini-2.5-flash-preview-tts")["contents"][0]["parts"]) == 1


def test_similar_ignores_spacing_and_punctuation():
    from studio.voice import similar

    assert similar("콩 사원, 이거 자네가 좀 봐 줘!", "콩사원, 이거 자네가 좀 봐줘.") > 0.95
    assert similar("한국 회사 시트콤의 한 장면입니다", "AI는 빨랐다. 하지만 이상한 걸 알아챈 건, 사람이었다.") < 0.4
