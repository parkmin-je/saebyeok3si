import json, sys, hashlib
from pathlib import Path
sys.path.insert(0, "/home/user/retro-romance-shorts")
from pipeline.episode.edit import tts
D = Path(sys.argv[1])
V = {"nar": "Charon", "son": "Iapetus", "old": "Algenib"}
for i, l in enumerate(json.load(open(D / "lines.json"))):
    say = f"[{l['tone']}] {l['text']}"
    out = D / "voice" / f"{i:02d}-{hashlib.md5((say+V[l['who']]).encode()).hexdigest()[:8]}.wav"
    tts(say, V[l["who"]], out, False)
    print(i, out.name, flush=True)
