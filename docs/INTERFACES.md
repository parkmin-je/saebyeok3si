# 인터페이스 명세서

> 문서 버전: v0.1 (2026-11-22) · 상태: 초안
> 계약의 원본은 [`schemas/`](../schemas/)의 JSON 스키마다. 이 문서와 스키마가 다르면 스키마가 맞다.

## 1. 계약 목록

| 계약 | 스키마 | 생산자 → 소비자 |
|---|---|---|
| 대본 | [`script.schema.json`](../schemas/script.schema.json) | S2 script (또는 사람) → S3, S4, S5, S8, P1, P2 |
| 타임라인 | [`timeline.schema.json`](../schemas/timeline.schema.json) | S5 timeline → S6, S7 |
| 런 매니페스트 | [`manifest.schema.json`](../schemas/manifest.schema.json) | runner → 모든 잡, 사람 |
| 게시 영수증 | [`publish-receipt.schema.json`](../schemas/publish-receipt.schema.json) | P1, P2 → publish 잡, 멱등성 검사 |
| 게이트 리포트 | §4 (아래) | G1~G3 → runner (재생성 피드백) |

모든 JSON 아티팩트는 최상위에 `schema_version` (semver 문자열)을 가진다.
소비자는 메이저 버전이 다르면 `FatalError`로 거부한다. 마이너 버전 차이는 허용 (필드 추가만 허용).

## 2. 대본 (script.json)

샘플: `scripts/samples/*.json`. 핵심 규칙:

| 필드 | 규칙 |
|---|---|
| `id` | `{era}-{NNN}` 형식, 유일 |
| `era` | `1900s` `1910s` … `2000s` 중 하나 |
| `target_duration_sec` | 45~59. `scenes[].duration_sec` 합과 같아야 한다 (G1 검사) |
| `aspect_ratio` | `"9:16"` 고정 |
| `characters[].key` | 대문자 한 글자. `image_prompt`의 `{A}`는 해당 `look`으로 치환된다 |
| `characters[].look` | 화면에 안 나오는 목소리 전용 인물(라디오 DJ 등)은 빈 문자열. 이 인물을 `image_prompt`에서 `{X}`로 부르면 G1 불합격 |
| `scenes` | 4~8개, `no`는 1부터 연속 |
| `scenes[].beat` | `hook` `memory` `conflict` `turn` `ending`. 첫 장면은 `hook`, 마지막은 `ending` |
| `scenes[].image_prompt` | 영어. 정의되지 않은 `{X}` 키 사용 금지 |
| `scenes[].dialogue[].speaker` | `characters[].key` 중 하나 |
| `scenes[].captions[]` | 한 줄 ≤ 14자 |
| `upload.yt_title` | ≤ 100자, `#shorts` 포함 |
| `upload.hashtags` | 3~10개, `#`으로 시작 |

스키마로 표현 못 하는 교차 규칙(합계, 키 참조, 금칙어)은 G1 게이트가 검사한다.

## 3. 스테이지 인터페이스

```python
from typing import Protocol
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class RunContext:
    run_id: str
    run_dir: Path                 # runs/{run_id}
    config: "PipelineConfig"      # 검증된 설정 (읽기 전용)
    providers: "ProviderRegistry" # 폴백 체인이 적용된 어댑터
    log: "StructuredLogger"
    budget: "BudgetTracker"       # charge(usd) 초과 시 BudgetError
    dry_run: bool

@dataclass(frozen=True)
class StageResult:
    outputs: list[Path]           # run_dir 기준 상대 경로
    cost_usd: float = 0.0
    meta: dict | None = None      # 매니페스트에 그대로 기록 (공급자명, 시드 등)

class Stage(Protocol):
    name: str                     # "script", "images", ...
    version: str                  # 로직이 바뀌면 올림 → input_hash가 바뀌어 재실행됨
    inputs: list[str]             # 읽는 파일 (glob 가능)
    outputs: list[str]            # 쓰는 파일
    def run(self, ctx: RunContext, feedback: list["Issue"] | None = None) -> StageResult: ...

class Gate(Protocol):
    name: str
    version: str
    regenerates: str              # 불합격 시 다시 돌릴 스테이지 이름
    def check(self, ctx: RunContext) -> "GateReport": ...
```

**스테이지 구현 규칙**

1. `inputs`에 선언하지 않은 파일을 읽지 않는다. `outputs`에 선언하지 않은 파일을 쓰지 않는다.
2. 파일은 반드시 `core.io.atomic_write()`로 쓴다.
3. 외부 호출은 `ctx.providers`를 통해서만 한다. SDK를 직접 import하지 않는다.
4. 오류는 `core.errors`의 클래스로만 던진다. 그 외 예외는 runner가 `FatalError`로 감싼다.
5. 같은 입력·같은 시드면 같은 출력을 내도록 시드를 매니페스트에 기록한다.

## 4. 게이트 리포트

```python
@dataclass(frozen=True)
class Issue:
    code: str          # "CAPTION_TOO_LONG", "DURATION_MISMATCH", "FACE_DISTORTED", ...
    target: str        # "scenes[3].captions[1]", "images/scene-04.png"
    message: str       # 재생성 프롬프트에 그대로 들어갈 한 문장
    severity: str      # "error" (불합격) | "warn" (기록만)

@dataclass(frozen=True)
class GateReport:
    passed: bool       # error 이슈가 0개면 True
    issues: list[Issue]
    regenerate_targets: list[str]  # 부분 재생성 대상 (예: ["scene-04"]). 비면 전체
```

### 게이트별 검사 항목

| 게이트 | 검사 | 코드 |
|---|---|---|
| G1 script | 스키마 | `SCHEMA_INVALID` |
| | 장면 길이 합 = target, 45~59초 | `DURATION_MISMATCH` |
| | 자막 줄 ≤ 14자 | `CAPTION_TOO_LONG` |
| | `{X}` 참조, speaker 참조 유효, `{X}` 인물의 look 비어 있지 않음 | `UNKNOWN_CHARACTER` |
| | 금칙어(`config/banned.yaml`) 미포함 | `BANNED_TERM` |
| | 내레이션 낭독 속도 추정 ≤ 장면 길이 (한국어 초당 약 6.5음절 기준) | `NARRATION_TOO_LONG` |
| | 최근 N편과 제목·로그라인 유사도 < 임계치 | `TOO_SIMILAR` |
| G2 images | 파일 존재, 1080×1920 이상, 9:16 | `IMAGE_INVALID` |
| | (선택) 비전 모델 검사: 글자·워터마크·손가락·얼굴 왜곡·시대착오 소품 | `IMAGE_ARTIFACT` |
| G3 video | ffprobe: 1080×1920, H.264, AAC, 30fps | `FORMAT_INVALID` |
| | 길이 45~59초 | `DURATION_OUT_OF_RANGE` |
| | 음량 -14 LUFS ±1, 피크 ≤ -1 dBTP | `LOUDNESS_OUT_OF_RANGE` |
| | 0.5초 이상 검은 화면·무음 구간 없음 | `BLACK_OR_SILENT` |
| | 크기 ≤ 100MB | `FILE_TOO_LARGE` |

## 5. 공급자 어댑터 인터페이스

모든 어댑터 메서드는 성공 시 결과 + `cost_usd`를 반환하고, 실패 시 `TransientError` / `ProviderError` / `FatalError` 중 하나만 던진다 (SDK 예외를 그대로 흘리지 않는다).

```python
class LLMProvider(Protocol):
    name: str
    def complete_json(self, system: str, user: str, schema: dict,
                      max_tokens: int, seed: int | None = None) -> tuple[dict, float]: ...
    # schema를 만족하는 dict만 반환. 파싱 실패는 ValidationError

class ImageProvider(Protocol):
    name: str
    def generate(self, prompt: str, negative: str, width: int, height: int,
                 seed: int, reference_images: list[Path] | None = None) -> tuple[bytes, float]: ...
    # reference_images: 인물 일관성용 (지원 안 하면 무시)

class TTSProvider(Protocol):
    name: str
    def synthesize(self, text: str, voice: "VoiceSpec") -> tuple[bytes, float]: ...
    # WAV 48kHz mono. 길이는 호출자가 측정

class MusicLibrary(Protocol):
    def pick_bgm(self, mood: str, min_duration_sec: float) -> "LicensedAudio": ...
    def pick_sfx(self, description: str) -> "LicensedAudio | None": ...
    # LicensedAudio = {path, source, license, attribution}

class Publisher(Protocol):
    platform: str  # "youtube" | "instagram"
    def find_existing(self, idempotency_key: str) -> "PublishReceipt | None": ...
    def publish(self, video: Path, cover: Path, meta: "PublishMeta",
                idempotency_key: str, publish_at: "datetime | None") -> "PublishReceipt": ...
    def check_auth(self) -> "AuthStatus": ...  # 토큰 유효성·만료일
```

```python
@dataclass(frozen=True)
class VoiceSpec:
    description: str   # 대본의 voice 문장 ("30대 남성, 담담한 목소리")
    voice_id: str      # config에서 description → 공급자 voice_id 매핑
    speed: float = 1.0

@dataclass(frozen=True)
class PublishMeta:
    title: str
    description: str
    hashtags: list[str]
    synthetic_content: bool = True   # NFR-C2
    privacy: str = "public"          # 미감사 YouTube 프로젝트에서는 강제로 private
```

### 폴백 체인 설정 예

```yaml
# config/pipeline.yaml
providers:
  llm:   [anthropic]
  image: [primary_image, fallback_image]
  tts:   [primary_tts, fallback_tts]
retry:   { max_attempts: 5, base_sec: 2, max_sec: 60 }
circuit: { failure_threshold: 3, cooldown_sec: 600 }
regen:   { script: 3, images: 3, video: 1 }
budget:  { per_episode_usd: 1.50 }
approval: auto          # auto | review
buffer:  { target: 3, min: 1 }
```

## 6. 타임라인 (timeline.json)

S5가 실측 음성 길이로 만든다. 렌더러는 이 파일만 보고 영상을 만든다 (대본을 다시 해석하지 않는다).

```json
{
  "schema_version": "1.0.0",
  "fps": 30, "width": 1080, "height": 1920,
  "duration_sec": 55.2,
  "scenes": [
    {
      "no": 1, "start": 0.0, "end": 5.0,
      "image": "images/scene-01.png",
      "motion": { "type": "zoom_in", "from": 1.0, "to": 1.12 },
      "transition_in": { "type": "fade", "sec": 0.0 },
      "voice": [ { "file": "audio/voice/scene-01.wav", "start": 0.4 } ],
      "captions": [ { "text": "20년 만에 예전 폴더폰을", "start": 0.4, "end": 2.6 } ]
    }
  ],
  "bgm": { "file": "assets/bgm/xxx.mp3", "gain_db": -18, "duck_under_voice_db": -8 },
  "sfx": [ { "file": "assets/sfx/flip-boot.wav", "start": 0.2, "gain_db": -6 } ]
}
```

장면 길이 규칙: `max(대본 duration_sec, 음성 길이 + 0.6초 여유)`. 합계가 59초를 넘으면 장면 길이를 비례 축소하되 음성보다 짧게 만들지 않는다. 그래도 넘으면 `QualityError(NARRATION_TOO_LONG)` → S2 재생성.

## 7. CLI

```
rrs validate [PATH...]                    # 스키마·G1 검사만 (대본 수동 작성 시)
rrs produce [--era 2000s] [--script FILE] [--dry-run]
rrs run RUN_ID --from STAGE               # 특정 스테이지부터 재실행 (하류 무효화)
rrs publish [--run RUN_ID] [--platform youtube|instagram] [--at ISO8601]
rrs approve RUN_ID | rrs reject RUN_ID --reason "..."
rrs status [RUN_ID]                       # 버퍼, 최근 런 상태, 토큰 만료일
```

종료 코드: `0` 성공, `1` 품질·검증 실패, `2` 공급자 실패, `3` 치명(설정·인증), `4` 예산 초과. 스케줄러와 알림은 이 코드로 분기한다.

## 8. 환경 변수

| 이름 | 용도 |
|---|---|
| `ANTHROPIC_API_KEY` | 대본 LLM |
| `IMAGE_API_KEY`, `TTS_API_KEY` | 공급자 확정 후 이름 확정 |
| `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` | 유튜브 업로드 |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | 인스타 릴스 게시 |
| `STORAGE_BUCKET`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`, `STORAGE_PUBLIC_BASE_URL` | 아티팩트 저장소 |
| `NOTIFY_WEBHOOK_URL` | 알림 |
| `RRS_TZ` | 기본 `Asia/Seoul` |
