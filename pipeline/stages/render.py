"""S6~S8: 오디오 믹스, 최종 렌더(자막·필름 질감), 표지 이미지.

일러스트 모드: 프레임은 pipeline/illustrated/<id>.html 을 capture.cjs로 찍어 만든다.
"""
import os
import subprocess
from pathlib import Path

from ..core import media
from ..core.errors import FatalError
from ..core.io import atomic_write, read_json
from .common import Ctx


def _ass_time(t: float) -> str:
    t = max(0.0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def write_ass(ctx: Ctx, tl: dict) -> Path:
    c = ctx.cfg["captions"]
    size, mv = int(c["size"]), int(c["margin_v"])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: N,{c['font_name']},{size},&H00ECF6FF,&H000000FF,&H000A0C10,&H64000000,-1,0,0,0,100,100,1,0,1,5,2,2,60,60,{mv},1
Style: D,{c['font_name']},{size},&H0098DCFF,&H000000FF,&H000A0C10,&H64000000,-1,0,0,0,100,100,1,0,1,5,2,2,60,60,{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for sc in tl["scenes"]:
        for cap in sc["captions"]:
            # 두 줄 묶음은 위아래로 쌓는다: row 0이 위
            margin = mv + (cap["rows"] - 1 - cap["row"]) * int(size * 1.35)
            style = "N" if cap["speaker"] == "N" else "D"
            lines.append(f"Dialogue: 0,{_ass_time(cap['start'])},{_ass_time(cap['end'])},{style},,0,0,{margin},,"
                         f"{{\\fad(180,180)}}{cap['text']}")
    p = ctx.run_dir / "render" / "captions.ass"
    atomic_write(p, head + "\n".join(lines) + "\n")
    return p


def frames(ctx: Ctx) -> Path:
    out = ctx.run_dir / "render" / "frames.mp4"
    if out.exists():
        return out
    html = ctx.repo / "pipeline" / "illustrated" / f"{ctx.script['id']}.html"
    if not html.exists():
        raise FatalError(f"일러스트 장면 파일이 없습니다: {html}")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name("frames.tmp.mp4")
    env = dict(os.environ)
    env["NODE_PATH"] = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    p = subprocess.run(["node", str(ctx.repo / "pipeline" / "illustrated" / "capture.cjs"), str(html),
                        str(ctx.run_dir / "timeline.json"), str(tmp), "30"], env=env)
    if p.returncode != 0:
        raise FatalError("프레임 렌더 실패")
    tmp.replace(out)
    return out


def mix(ctx: Ctx, tl: dict) -> Path:
    """음성 배치 + 배경음악(음성 아래로 덕킹) + -14 LUFS 정규화."""
    out = ctx.run_dir / "audio" / "mix.wav"
    if out.exists():
        return out
    voices = [(v["file"], v["start"]) for sc in tl["scenes"] for v in sc["voice"]]
    dur = tl["duration_sec"]
    args, parts = [], []
    for i, (f, st) in enumerate(voices):
        args += ["-i", str(ctx.run_dir / f)]
        ms = int(st * 1000)
        parts.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms},apad[v{i}]")
    n = len(voices)
    bgm = tl["bgm"]
    args += ["-i", str(ctx.run_dir / bgm["file"])]
    vin = "".join(f"[v{i}]" for i in range(n))
    fc = ";".join(parts) + (
        f";{vin}amix=inputs={n}:normalize=0:duration=longest,atrim=0:{dur},"
        f"acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120,"
        f"aecho=0.8:0.5:40:0.12,asplit=2[voice][key]"
        f";[{n}:a]aresample=48000,volume={bgm['gain_db']}dB,atrim=0:{dur}[bg]"
        f";[bg][key]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=400[bgd]"
        f";[voice][bgd]amix=inputs=2:normalize=0:duration=first,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[out]")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name("mix.tmp.wav")
    media.run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", fc, "-map", "[out]", "-ac", "2",
               "-t", str(dur), str(tmp)])
    tmp.replace(out)
    return out


def final(ctx: Ctx, tl: dict, frames_mp4: Path, mix_wav: Path) -> Path:
    out = ctx.run_dir / "render" / "final.mp4"
    ass = write_ass(ctx, tl)
    grade = ctx.cfg["eras"].get(ctx.script["era"], ctx.cfg["eras"]["default"])
    fontsdir = ctx.repo / Path(ctx.cfg["captions"]["font"]).parent
    vf = f"{grade},subtitles={ass}:fontsdir={fontsdir},format=yuv420p"
    tmp = out.with_name("final.tmp.mp4")
    media.run(["ffmpeg", "-y", "-v", "error", "-i", str(frames_mp4), "-i", str(mix_wav), "-vf", vf,
               "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "16M", "-bufsize", "32M", "-profile:v", "high",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
               "-movflags", "+faststart", "-shortest", str(tmp)])
    tmp.replace(out)
    return out


def cover(ctx: Ctx, frames_mp4: Path) -> Path:
    out = ctx.run_dir / "render" / "cover.jpg"
    text = ctx.script["upload"]["cover_text"]
    font = ctx.repo / ctx.cfg["captions"]["font"]
    grade = ctx.cfg["eras"].get(ctx.script["era"], ctx.cfg["eras"]["default"])
    tl = read_json(ctx.run_dir / "timeline.json")
    at = tl["scenes"][-1]["start"] + 1.5  # 마지막 장면: 대문 앞 들꽃
    media.run(["ffmpeg", "-y", "-v", "error", "-ss", str(at), "-i", str(frames_mp4), "-frames:v", "1", "-vf",
               f"{grade},drawbox=y=1180:w=iw:h=330:color=black@0.35:t=fill,"
               f"drawtext=fontfile={font}:text='{text}':fontsize=96:fontcolor=0xF4F0E8:"
               f"borderw=5:bordercolor=0x101418:x=(w-text_w)/2:y=1290", "-q:v", "2", str(out)])
    return out
