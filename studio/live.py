"""마지막 무료 목소리: Gemini Live 네이티브 오디오 (TTS 모델 한도와 따로 센다).

한 줄씩만 녹음한다. 대사를 바꿔 말할 때가 있으므로 voice.heard 로 꼭 확인한다.
"""

import asyncio
import base64
import json
import os
import ssl

import numpy as np

MODELS = os.environ.get("GEMINI_LIVE_MODELS", "gemini-2.5-flash-native-audio-latest").split(",")
URL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
ACTOR = "너는 한국어 성우다. 사용자가 준 대사를 한 글자도 바꾸지 말고 그대로, 지시된 감정으로 한 번만 읽어라. 다른 말은 절대 하지 마라."


def hangul_ai(text: str) -> str:
    """'AI' 를 '에이아이' 로 (영문 약자를 흘려 읽거나 빼먹는다)."""
    return text.replace("AI", "에이아이 ")


async def _say(model, voice_name, text, how) -> np.ndarray:
    import websockets  # 선택 의존성: pip install websockets

    ca = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else None)
    ctx = ssl.create_default_context(cafile=ca)
    setup = {
        "setup": {
            "model": f"models/{model}",
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_name}}},
            },
            "systemInstruction": {"parts": [{"text": ACTOR}]},
        }
    }
    turn = {"clientContent": {"turns": [{"role": "user", "parts": [{"text": f"감정: {how}\n대사: {text}"}]}], "turnComplete": True}}
    pcm = b""
    async with websockets.connect(URL, additional_headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, ssl=ctx, max_size=None) as ws:
        await ws.send(json.dumps(setup))
        await ws.recv()
        await ws.send(json.dumps(turn))
        async for m in ws:
            sc = json.loads(m).get("serverContent", {})
            for p in sc.get("modelTurn", {}).get("parts", []):
                if "inlineData" in p:
                    pcm += base64.b64decode(p["inlineData"]["data"])
            if sc.get("turnComplete"):
                break
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768  # 24kHz


def say(voice_name: str, text: str, how: str) -> np.ndarray | None:
    for model in MODELS:
        try:
            x = asyncio.run(asyncio.wait_for(_say(model, voice_name, hangul_ai(text), how), 120))
        except Exception:  # noqa: BLE001 - 다음 모델로
            continue
        if len(x):
            return x
    return None
