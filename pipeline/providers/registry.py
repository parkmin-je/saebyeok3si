"""설정에서 공급자 폴백 체인을 만든다."""
from ..core.errors import FatalError, ProviderError
from ..core.retry import with_retry
from . import fake, gemini


class Chain:
    """첫 공급자부터 시도하고, ProviderError면 다음 공급자로 넘어간다."""

    def __init__(self, kind: str, providers: list, log=print):
        if not providers:
            raise FatalError(f"{kind} 공급자가 설정되지 않았습니다")
        self.kind, self.providers, self.log = kind, providers, log
        self.dead: set[str] = set()   # 이번 실행에서 한도 소진 등으로 실패한 공급자는 다시 시도하지 않는다

    def call(self, method: str, *args, **kwargs):
        last = None
        for p in self.providers:
            if p.name in self.dead and p is not self.providers[-1]:
                continue
            try:
                out = with_retry(lambda: getattr(p, method)(*args, **kwargs), log=self.log,
                                 label=f"{p.name}.{method}")
                return out, p.name
            except ProviderError as e:
                self.log(f"[fallback] {p.name} 실패 → 다음 공급자: {e}")
                self.dead.add(p.name)
                last = e
        raise ProviderError(f"{self.kind}: 모든 공급자 실패: {last}")


def build(cfg: dict, quality: str, use_fake: bool, log=print) -> dict[str, Chain]:
    if use_fake:
        return {"image": Chain("image", [fake.FakeImage()], log),
                "video": Chain("video", [fake.FakeVideo()], log),
                "tts": Chain("tts", [fake.FakeTTS()], log)}
    g = cfg["providers"]["gemini"]
    images = [gemini.NanoBananaImage(m["model"], m["usd_per_image"]) for m in g["image"]]
    video_tiers = g["video"][quality]
    videos = [gemini.Veo(m["model"], m["usd_per_sec"], m.get("resolution", "1080p")) for m in video_tiers]
    tts = [gemini.GeminiTTS(m["model"], m["usd_per_char"]) for m in g["tts"]]
    return {"image": Chain("image", images, log), "video": Chain("video", videos, log),
            "tts": Chain("tts", tts, log)}
