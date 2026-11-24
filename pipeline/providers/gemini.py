"""Google Gemini API 어댑터: 나노바나나(이미지), Veo 3.1(영상), Gemini TTS(음성).

키: GEMINI_API_KEY. 모델 ID는 config/pipeline.yaml에서 바꾼다.
REST만 쓴다 (SDK 직접 의존 없음, NFR-O5).
"""
import base64
import os
import subprocess
import tempfile
import time
from pathlib import Path

import requests

from ..core.errors import FatalError, ProviderError, TransientError
from .base import VoiceSpec

API = "https://generativelanguage.googleapis.com/v1beta"


def _key() -> str:
    k = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not k:
        raise FatalError("GEMINI_API_KEY가 설정되지 않았습니다")
    return k


def _check(r: requests.Response) -> dict:
    if r.status_code == 429 and "PerDay" in r.text:
        raise ProviderError(f"일일 무료 한도 소진 HTTP 429: {r.text[:200]}")
    if r.status_code == 429 or r.status_code >= 500:
        ra = r.headers.get("Retry-After")
        raise TransientError(f"HTTP {r.status_code}: {r.text[:300]}", float(ra) if ra else None)
    if r.status_code in (401, 403):
        raise FatalError(f"인증/권한 오류 HTTP {r.status_code}: {r.text[:300]}")
    if r.status_code == 404:
        raise ProviderError(f"모델 없음 HTTP 404: {r.text[:300]}")
    if r.status_code >= 400:
        raise FatalError(f"요청 오류 HTTP {r.status_code}: {r.text[:500]}")
    return r.json()


def _post(path: str, body: dict, timeout: int = 300) -> dict:
    try:
        r = requests.post(f"{API}/{path}", json=body, timeout=timeout,
                          headers={"x-goog-api-key": _key()})
    except requests.RequestException as e:
        raise TransientError(str(e)) from e
    return _check(r)


def _get(url: str, timeout: int = 120, raw: bool = False):
    try:
        r = requests.get(url, timeout=timeout, headers={"x-goog-api-key": _key()},
                         allow_redirects=True)
    except requests.RequestException as e:
        raise TransientError(str(e)) from e
    if raw:
        if r.status_code >= 400:
            _check(r)
        return r.content
    return _check(r)


def _inline_parts(resp: dict) -> list[dict]:
    cands = resp.get("candidates") or []
    if not cands:
        fb = resp.get("promptFeedback", {})
        raise FatalError(f"응답에 후보가 없습니다 (차단 사유: {fb.get('blockReason')})")
    return [p["inlineData"] for p in cands[0].get("content", {}).get("parts", []) if "inlineData" in p]


class NanoBananaImage:
    """Gemini 이미지 모델 (나노바나나 / 나노바나나 Pro)."""

    def __init__(self, model: str, usd_per_image: float):
        self.model = model
        self.name = f"gemini:{model}"
        self.usd = usd_per_image

    def generate(self, prompt, negative, width, height, seed, reference_images=None):
        parts = []
        for ref in reference_images or []:
            parts.append({"inlineData": {"mimeType": "image/png",
                                         "data": base64.b64encode(Path(ref).read_bytes()).decode()}})
        text = prompt
        if reference_images:
            text = ("Use the attached reference image(s) to keep each character's face, hair and "
                    "clothing exactly consistent. " + text)
        if negative:
            text += f"\nAvoid: {negative}."
        parts.append({"text": text})
        body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {"aspectRatio": "9:16"},
                "seed": seed,
            },
        }
        imgs = _inline_parts(_post(f"models/{self.model}:generateContent", body))
        if not imgs:
            raise TransientError("이미지가 반환되지 않았습니다")
        return base64.b64decode(imgs[0]["data"]), self.usd


class Veo:
    """Veo 이미지→영상. predictLongRunning 후 폴링."""

    def __init__(self, model: str, usd_per_sec: float, resolution: str = "1080p",
                 poll_sec: int = 10, timeout_sec: int = 900):
        self.model = model
        self.name = f"gemini:{model}"
        self.usd_per_sec = usd_per_sec
        self.resolution = resolution
        self.poll_sec = poll_sec
        self.timeout_sec = timeout_sec

    def animate(self, image, prompt, negative, duration_sec, seed):
        body = {
            "instances": [{
                "prompt": prompt,
                "image": {"bytesBase64Encoded": base64.b64encode(Path(image).read_bytes()).decode(),
                          "mimeType": "image/png"},
            }],
            "parameters": {
                "aspectRatio": "9:16",
                "durationSeconds": duration_sec,
                "resolution": self.resolution,
                "negativePrompt": negative,
                "personGeneration": "allow_adult",
                "sampleCount": 1,
            },
        }
        op = _post(f"models/{self.model}:predictLongRunning", body)
        name = op["name"]
        deadline = time.time() + self.timeout_sec
        while not op.get("done"):
            if time.time() > deadline:
                raise TransientError(f"Veo 작업 시간 초과: {name}")
            time.sleep(self.poll_sec)
            op = _get(f"{API}/{name}")
        if "error" in op:
            raise FatalError(f"Veo 실패: {op['error']}")
        resp = op.get("response", {}).get("generateVideoResponse", {})
        samples = resp.get("generatedSamples") or []
        if not samples:
            raise FatalError(f"Veo가 영상을 돌려주지 않았습니다 (필터링 가능성): {resp}")
        video = samples[0]["video"]
        data = base64.b64decode(video["bytesBase64Encoded"]) if "bytesBase64Encoded" in video \
            else _get(video["uri"], timeout=300, raw=True)
        return data, self.usd_per_sec * duration_sec


class GeminiTTS:
    """Gemini TTS (무료 등급에서 gemini-3.8-flash-tts 사용 가능, 2026-11 확인).

    주의: 이 모델은 "~한 목소리로 읽어 주세요" 같은 지시문까지 소리 내어 읽는다.
    그래서 본문만 보내고, 목소리 성격은 voice_id(프리셋)와 속도(atempo)로만 조절한다.
    """

    def __init__(self, model: str, usd_per_char: float):
        self.model = model
        self.name = f"gemini:{model}"
        self.usd_per_char = usd_per_char

    def synthesize(self, text: str, voice: VoiceSpec):
        body = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice.voice_id}}},
            },
        }
        auds = _inline_parts(_post(f"models/{self.model}:generateContent", body))
        if not auds:
            raise TransientError("음성이 반환되지 않았습니다")
        raw = base64.b64decode(auds[0]["data"])
        mime = auds[0].get("mimeType", "")
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "in", Path(d) / "a.wav"
            src.write_bytes(raw)
            if "wav" in mime:
                fmt = []
            else:  # audio/L16;rate=24000 같은 raw PCM
                rate = mime.split("rate=")[1].split(";")[0] if "rate=" in mime else "24000"
                fmt = ["-f", "s16le", "-ar", rate, "-ac", "1"]
            trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
            atempo = f",atempo={voice.speed}" if voice.speed != 1.0 else ""
            subprocess.run(["ffmpeg", "-y", "-v", "error", *fmt, "-i", str(src), "-af", trim + atempo,
                            "-ar", "48000", "-ac", "1", str(dst)], check=True)
            return dst.read_bytes(), self.usd_per_char * len(text)
