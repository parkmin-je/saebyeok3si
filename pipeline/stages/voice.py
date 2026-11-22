"""S4 voice: 장면별 내레이션·대사를 줄 단위로 합성하고 실측 길이를 기록한다."""
import re

from ..core import media
from ..core.io import atomic_write, write_json
from ..providers.base import VoiceSpec
from .common import Ctx, nn

name = "voice"
OLD = re.compile(r"(6|7|8|9)0대|노년|할머니|할아버지")
MID = re.compile(r"(3|4|5)0대|중년")


def pick_voice(desc: str, voices: dict) -> VoiceSpec:
    female = "여성" in desc or "여자" in desc
    age = "_old" if OLD.search(desc) else "_mid" if MID.search(desc) else ""
    speed = float(voices.get("speed_old", 1.0)) if age == "_old" else 1.0
    return VoiceSpec(desc, voices[("female" if female else "male") + age], speed)


def segments(scene: dict, script: dict) -> list[dict]:
    voice_of = {c["key"]: c["voice"] for c in script["characters"]}
    segs = []
    if scene["narration"].strip():
        segs.append({"speaker": "N", "text": scene["narration"].strip(),
                     "voice": script["style"]["narrator_voice"]})
    for d in scene["dialogue"]:
        segs.append({"speaker": d["speaker"], "text": d["line"].strip(), "voice": voice_of[d["speaker"]]})
    return segs


def run(ctx: Ctx) -> None:
    s = ctx.script
    out = ctx.run_dir / "audio" / "voice"
    index = []
    for sc in s["scenes"]:
        for i, seg in enumerate(segments(sc, s), 1):
            p = out / f"scene-{nn(sc['no'])}-{i}.wav"
            if not p.exists():
                spec = pick_voice(seg["voice"], ctx.cfg["voices"])
                (data, cost), prov = ctx.providers["tts"].call("synthesize", seg["text"], spec)
                atomic_write(p, data)
                ctx.charge(cost, f"장면 {sc['no']} 음성 {i} ({prov}, {spec.voice_id})")
            index.append({"no": sc["no"], "seq": i, "speaker": seg["speaker"], "text": seg["text"],
                          "file": f"audio/voice/{p.name}", "duration_sec": round(media.duration(p), 3)})
    write_json(out / "index.json", {"schema_version": "1.0.0", "segments": index})
