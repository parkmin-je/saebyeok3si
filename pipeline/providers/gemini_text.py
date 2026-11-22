"""Gemini 텍스트 모델로 JSON 생성 (무료 등급). LLMProvider 인터페이스 (INTERFACES.md §5)."""
import json

from ..core.errors import ValidationError
from .gemini import _post


class GeminiText:
    def __init__(self, model: str):
        self.model = model
        self.name = f"gemini:{model}"

    def complete_json(self, system: str, user: str, schema: dict | None = None,
                      max_tokens: int = 8192, seed: int | None = None):
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": max_tokens,
                                 "temperature": 1.0, **({"seed": seed} if seed is not None else {})},
        }
        r = _post(f"models/{self.model}:generateContent", body)
        try:
            text = "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"])
            return json.loads(text), 0.0
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ValidationError(f"JSON 파싱 실패: {e}; 응답: {json.dumps(r, ensure_ascii=False)[:300]}") from e
