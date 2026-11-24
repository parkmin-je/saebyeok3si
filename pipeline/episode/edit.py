"""연재 숏드라마 한 화 편집기: 컷 영상 + 대사(TTS) + 굵은 자막 + 효과음 + 배경음 + 폴더폰 문자 화면 → final.mp4

사용: python -m pipeline.episode.edit <edit.json> <out_dir> [--fake-voice]

edit.json
{
  "id": "ep01", "series": "우리가 열여덟이던 겨울", "episode": 1, "title": "물어내", "next": "EP.02 남의 폰",
  "cast": {"seojin": {"name": "서진", "voice": "Leda", "color": "FFC8D8"}, ...},
  "music": "piano_minor",
  "shots": [
    {"src": "clips/s02.mp4", "in": 0.4, "dur": 2.5,
     "lines": [{"who": "seojin", "text": "야. 사과 안 해?", "at": 0.3, "inner": false}],
     "sfx": [{"name": "crack", "at": 0.1}], "phone": "채린: 도윤아, 오늘 4시 옥상.", "slow": 1.0}
  ]
}
src가 .png면 깊이 없이 천천히 밀고 들어가는 카메라 움직임으로 만든다.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from ..core import media
from ..stages.music import compose
from .sfx import BANK, SR

REPO = Path(__file__).resolve().parents[2]
FONT_DIR = REPO / "assets" / "fonts"
W, H, FPS = 1080, 1920, 30
GRADE = ("eq=contrast=1.05:saturation=0.9:gamma=0.98,"
         "colorbalance=rs=0.03:gs=0.01:bs=-0.03:rh=0.02:bh=-0.02,"
         "vignette=PI/5,noise=alls=3:allf=t")


def run(cmd):
    subprocess.run(cmd, check=True)


def read_wav(p: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def tts(text: str, voice: str, out: Path, fake: bool) -> Path:
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    if fake:
        dur = max(0.8, len(text) / 6.5)
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=f=220:d={dur:.2f}", "-af", "volume=0.2",
             "-ar", "48000", "-ac", "1", str(out)])
        return out
    from ..providers.base import VoiceSpec
    from ..providers.gemini import GeminiTTS
    from ..core.retry import with_retry
    import yaml
    cfg = yaml.safe_load((REPO / "config" / "pipeline.yaml").read_text(encoding="utf-8"))
    models = [m["model"] for m in cfg["providers"]["gemini"]["tts"]]
    last = None
    for m in models:
        try:
            data, _ = with_retry(lambda: GeminiTTS(m, 0.0).synthesize(text, VoiceSpec("", voice)), label=f"tts {m}")
            out.write_bytes(data)
            return out
        except Exception as e:  # noqa: BLE001
            last = e
    raise RuntimeError(f"TTS 실패: {last}")


def phone_png(text: str, out: Path) -> Path:
    """2000년대 폴더폰 LCD 문자 화면 (화면 중앙 큼직하게)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 170, 560, 910, 1260
    d.rounded_rectangle((x0 - 40, y0 - 60, x1 + 40, y1 + 60), 70, fill=(176, 182, 190, 255))  # 은색 몸체
    d.rounded_rectangle((x0, y0, x1, y1), 24, fill=(18, 24, 40, 255))
    lcd = (x0 + 24, y0 + 24, x1 - 24, y1 - 24)
    d.rectangle(lcd, fill=(156, 205, 255, 255))
    head = ImageFont.truetype(str(FONT_DIR / "NanumGothicExtraBold.ttf"), 46)
    body = ImageFont.truetype(str(FONT_DIR / "NanumGothicExtraBold.ttf"), 58)
    d.rectangle((lcd[0], lcd[1], lcd[2], lcd[1] + 78), fill=(40, 70, 140, 255))
    d.text((lcd[0] + 24, lcd[1] + 14), "새 메시지 1건", font=head, fill=(255, 255, 255, 255))
    # 줄바꿈: 11자 단위
    lines, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= 11 or ch == "\n":
            lines.append(cur.strip())
            cur = ""
    if cur.strip():
        lines.append(cur.strip())
    y = lcd[1] + 120
    for ln in lines[:7]:
        d.text((lcd[0] + 30, y), ln, font=body, fill=(10, 20, 50, 255))
        y += 80
    shadow = img.filter(ImageFilter.GaussianBlur(18))
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    base.alpha_composite(shadow)
    base.alpha_composite(img)
    base.save(out)
    return out


def shot_video(sh: dict, dur: float, out: Path) -> None:
    src = REPO / sh["src"] if not Path(sh["src"]).is_absolute() else Path(sh["src"])
    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    if src.suffix.lower() in (".png", ".jpg", ".jpeg"):
        z = sh.get("zoom", 0.06)
        vf = (f"{cover},zoompan=z='1+{z}*on/({dur}*{FPS})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":d=1:s={W}x{H}:fps={FPS}")
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(src), "-t", f"{dur:.3f}", "-vf", vf,
             "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)])
        return
    start = float(sh.get("in", 0))
    avail = max(0.1, media.duration(src) - start)
    slow = float(sh.get("slow", 1.0))
    need = dur / slow
    if need > avail:   # 클립이 모자라면 먼저 최대 1.4배까지 느리게, 그래도 모자라면 마지막 프레임 유지
        slow = min(1.4, dur / avail)
    pad = max(0.0, dur - avail * slow)
    # 16fps 생성 컷을 움직임 보간으로 30fps (그냥 복제하면 뚝뚝 끊겨 보임)
    interp = f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" if media_fps(src) < 25 else f"fps={FPS}"
    vf = f"setpts={slow:.4f}*(PTS-STARTPTS),{interp},{cover},tpad=stop_mode=clone:stop_duration={pad + 0.1:.3f}"
    if sh.get("shake"):   # 충격 장면 카메라 흔들림 (처음 0.6초, 점점 잦아듦)
        a = float(sh["shake"]) if not isinstance(sh["shake"], bool) else 18
        t0 = float(sh.get("shake_at", 0))
        k = f"gte(t\\,{t0})*{a}*exp(-(t-{t0})*5)"
        vf += (f",scale={W + 2 * int(a)}:{H + 2 * int(a)},crop={W}:{H}:"
               f"x='{int(a)}+{k}*sin(t*67)':y='{int(a)}+{k}*cos(t*53)'")
    if sh.get("flash"):   # 컷 첫 순간 하얗게 번쩍
        vf += ",eq=brightness=0.45:enable='lt(t,0.07)'"
    z = float(sh.get("push", 0.04))   # 컷마다 살짝 밀고 들어가는 카메라 (화면이 멈춰 보이지 않게)
    if z:
        vf += (f",zoompan=z='1+{z}*on/({dur}*{FPS})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
               f":d=1:s={W}x{H}:fps={FPS}")
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{dur:.3f}", "-vf", vf,
         "-an", "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)])


def media_fps(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()
    a, _, b = r.partition("/")
    return float(a) / float(b or 1) if a else 30.0


def ass_time(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def bgr(hex_rgb: str) -> str:
    r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
    return f"&H00{b}{g}{r}"


def wrap(text: str, n: int = 13) -> str:
    """한 줄 13자 안팎, 어절 단위로 두 줄까지."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > n:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    return r"\N".join(lines)


def main(spec_path: str, out_dir: str, fake: bool = False) -> Path:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    out = Path(out_dir)
    (out / "shots").mkdir(parents=True, exist_ok=True)
    cast = spec["cast"]
    # 1) 대사 음성 → 컷 길이 결정
    timeline, t = [], 0.0
    for i, sh in enumerate(spec["shots"]):
        lines = []
        end_need = float(sh.get("dur", 2.5))
        for k, ln in enumerate(sh.get("lines", [])):
            # 감정 태그(예: [annoyed])를 앞에 붙이면 Gemini TTS가 태그는 읽지 않고 말투만 바꾼다
            say = f"[{ln['tone']}] {ln['text']}" if ln.get("tone") else ln["text"]
            import hashlib
            key = hashlib.md5(f"{say}|{cast[ln['who']]['voice']}".encode()).hexdigest()[:8]
            wav = tts(say, cast[ln["who"]]["voice"], out / "voice" / f"{i:02d}-{k}-{key}.wav", fake)
            d = media.duration(wav)
            lines.append({**ln, "wav": wav, "len": d})
            end_need = max(end_need, float(ln.get("at", 0.2)) + d + 0.12)
        timeline.append({"i": i, "start": t, "dur": end_need, "lines": lines, "sh": sh})
        t += end_need
    total = t
    # 2) 컷 영상
    clips = []
    for c in timeline:
        p = out / "shots" / f"{c['i']:02d}.mp4"
        shot_video(c["sh"], c["dur"], p)
        clips.append(p)
    listf = out / "shots" / "list.txt"
    listf.write_text("".join(f"file '{p.resolve()}'\n" for p in clips))
    cat = out / "cat.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listf), "-c", "copy", str(cat)])
    # 3) 오디오: 대사 + 효과음 + 음악(대사 나올 때 낮춤)
    n = int((total + 0.5) * SR)
    voice, fx = np.zeros(n), np.zeros(n)
    for c in timeline:
        for ln in c["lines"]:
            a = read_wav(ln["wav"])
            s = int((c["start"] + float(ln.get("at", 0.2))) * SR)
            voice[s:s + len(a)] += a[: max(0, n - s)]
        for fxs in c["sh"].get("sfx", []):
            a = BANK[fxs["name"]]() * float(fxs.get("gain", 1.0))
            s = int((c["start"] + float(fxs.get("at", 0))) * SR)
            fx[s:s + len(a)] += a[: max(0, n - s)]
    if spec.get("cues"):   # 장면별 음악: {"shot": 컷 번호, "type": tension|banter|flutter|stop, "at"?: 컷 안 초}
        from .score import compose_cues
        mus = compose_cues([{"t": timeline[min(c["shot"], len(timeline) - 1)]["start"] + float(c.get("at", 0)),
                             "type": c["type"], "gain": c.get("gain", 1.0)} for c in spec["cues"]], total + 0.5)
    else:
        mus = compose(total + 0.5, preset=spec.get("music", "piano_minor"))
    mus = np.interp(np.arange(n), np.linspace(0, n, len(mus)), mus) if len(mus) != n else mus
    env = np.convolve((np.abs(voice) > 0.01).astype(float), np.ones(SR // 4) / (SR // 4), "same")
    duck = 1 - 0.65 * np.clip(env * 3, 0, 1)
    rng = np.random.default_rng(7)   # 바깥 공기·교실 웅성임 느낌의 낮은 환경음 (완전 무음 구간 없애기)
    amb = np.convolve(rng.standard_normal(n), np.ones(60) / 60, "same")
    amb *= (0.6 + 0.4 * np.sin(np.arange(n) / SR * 0.7)) / max(1e-9, np.abs(amb).max())
    mix = voice * 1.0 + fx * 0.8 + mus * float(spec.get("music_gain", 0.22)) * duck + amb * float(spec.get("ambient", 0.05))
    mix /= max(1e-9, np.abs(mix).max()) / 0.9
    raw = out / "mix.f32"
    raw.write_bytes(mix.astype(np.float32).tobytes())
    mixwav = out / "mix.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw), "-af",
         "loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.84", "-ar", "48000", "-ac", "2", str(mixwav)])
    # 4) 자막 (굵은 고딕, 인물 색, 화면 아래 3분의 1 위쪽) + 다음 화 예고
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: L,NanumSquare ExtraBold,78,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,70,560,1
Style: I,NanumSquare ExtraBold,66,&H00E0E0E0,&H000000FF,&H00000000,&H96000000,-1,1,0,0,100,100,0,0,1,6,2,2,70,70,560,1
Style: T,NanumSquare ExtraBold,64,&H00FFFFFF,&H000000FF,&H00000000,&HB4000000,-1,0,0,0,100,100,0,0,3,10,0,8,60,60,180,1
Style: K,NanumSquare ExtraBold,96,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,9,4,8,60,60,230,1
Style: N,NanumSquare ExtraBold,96,&H0000D7FF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,8,4,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    hook = spec.get("hook")   # 첫 1~3초 훅 문구 (소리 없이 봐도 상황이 읽히게)
    t0 = 2.8 if hook else 0
    ev = [f"Dialogue: 0,{ass_time(t0)},{ass_time(t0 + 2.4)},T,,0,0,0,,{{\\fad(150,300)}}"
          f"{spec['series']} EP.{spec['episode']:02d}"]
    if hook:
        hl = [y for x in hook.split("|") for y in wrap(x, 10).split(r"\N")]
        txt = r"\N".join(f"{{\\c&H0000D7FF&}}{x}" if i == len(hl) - 1 else x for i, x in enumerate(hl))
        ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(t0)},K,,0,0,0,,{{\\fad(0,200)}}{txt}")
    for c in timeline:
        for ln in c["lines"]:
            s = c["start"] + float(ln.get("at", 0.2))
            e = s + ln["len"] + 0.15
            col = cast[ln["who"]].get("color", "FFFFFF")
            style = "I" if ln.get("inner") else "L"
            txt = wrap(ln["text"])
            if ln.get("inner"):
                txt = f"({txt})"
            ev.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},{style},,0,0,0,,"
                      f"{{\\c{bgr(col)}\\fad(40,80)\\fscx118\\fscy118\\t(0,110,\\fscx100\\fscy100)}}{txt}")
    if spec.get("next"):
        ev.append(f"Dialogue: 1,{ass_time(total - 2.2)},{ass_time(total)},N,,0,0,0,,{{\\fad(200,0)}}{spec['next']}")
    assf = out / "captions.ass"
    assf.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
    # 5) 폴더폰 문자 화면 오버레이
    inputs, fc, last = ["-i", str(cat)], [f"[0:v]{GRADE}[g0]"], "[g0]"
    k = 1
    for c in timeline:
        if c["sh"].get("phone"):
            png = phone_png(c["sh"]["phone"], out / f"phone-{c['i']:02d}.png")
            inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", str(png)]
            s, e = c["start"] + 0.3, c["start"] + c["dur"]
            fc.append(f"{last}[{k}:v]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'[o{k}]")
            last = f"[o{k}]"
            k += 1
    fonts = str(FONT_DIR).replace(":", r"\:")
    fc.append(f"{last}ass={assf}:fontsdir={fonts}[v]")
    final = out / "final.mp4"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-i", str(mixwav), "-filter_complex", ";".join(fc),
         "-map", "[v]", "-map", f"{k}:a", "-t", f"{total:.2f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "slow",
         "-crf", "21", "-maxrate", "9M", "-bufsize", "18M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)])
    print(f"[edit] {final} {total:.1f}s, 컷 {len(clips)}개", flush=True)
    return final


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], "--fake-voice" in a)
