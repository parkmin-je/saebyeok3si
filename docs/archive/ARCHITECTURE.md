# 아키텍처 설계서

> 문서 버전: v0.1 (2026-11-22) · 상태: 초안
> 요구사항: [REQUIREMENTS.md](REQUIREMENTS.md) · 인터페이스: [INTERFACES.md](INTERFACES.md)

## 1. 설계 원칙

"깨지지 않는" 파이프라인을 위해 모든 설계는 아래 7가지 원칙을 따른다. 각 원칙 옆은 대응 요구사항이다.

1. **제작과 게시를 분리한다** (NFR-R1). 제작은 미리, 게시는 정시에. 제작이 늦거나 실패해도 버퍼에 있는 완성본으로 슬롯을 채운다.
2. **스테이지는 파일 계약만으로 대화한다** (NFR-O5). 스테이지끼리 메모리 객체를 넘기지 않는다. 입력 파일을 읽고 출력 파일을 쓴다. 각 파일은 JSON 스키마로 검증된다.
3. **모든 스테이지는 멱등이다** (NFR-R2). 같은 입력이면 다시 돌려도 같은 결과(또는 이미 만든 결과 재사용). 입력 해시가 같고 출력이 검증되면 건너뛴다.
4. **쓰기는 원자적이다** (NFR-R2). `파일.tmp`에 쓰고 검증 후 `rename`. 반쯤 쓰인 파일은 존재할 수 없다.
5. **오류는 분류해서 다르게 처리한다** (NFR-R5). 일시 오류는 재시도, 품질 오류는 재생성, 치명 오류는 즉시 중단·알림.
6. **외부 의존은 어댑터 뒤에 숨긴다** (NFR-R6). LLM·이미지·TTS·업로드 모두 인터페이스 + 폴백 체인.
7. **게시는 정확히 한 번** (NFR-R3). 멱등 키로 "이미 올렸는지"를 먼저 확인하고, 올린 직후 영수증을 기록한다.

## 2. 전체 구조

```
                 ┌───────────────────────── 스케줄러 (GitHub Actions cron) ─────────────────────────┐
                 │                                                                                 │
        [produce 잡: 버퍼가 목표치보다 적으면 실행]                         [publish 잡: 슬롯 시각마다 실행]
                 │                                                                                 │
                 ▼                                                                                 ▼
  ┌──────────── 제작 런 (run_id) ───────────────┐                                ┌──── 게시 런 ────┐
  │ S1 plan → S2 script → G1 script gate        │                                │ P0 pick ready   │
  │   → S3 images → G2 image gate               │   완성본 + 매니페스트           │ P1 youtube      │
  │   → S4 voice → S5 timeline                  │ ─────────────────────────────▶ │ P2 instagram    │
  │   → S6 audio mix → S7 render → S8 cover     │   (버퍼: status = ready)        │ P3 report       │
  │   → G3 video gate → (review 모드면 승인 대기)│                                └─────────────────┘
  └─────────────────────────────────────────────┘
                 │                     │
                 ▼                     ▼
          아티팩트 저장소        알림 채널 (성공/실패/승인 요청)
     (runs/{run_id}/ + 오브젝트 스토리지)
```

## 3. 스테이지 목록

| ID | 스테이지 | 입력 | 출력 | 외부 의존 |
|---|---|---|---|---|
| S1 | plan | `config/*.yaml`, 게시 이력 | `plan.json` (시대, 테마, 소재 금지 목록) | 없음 |
| S2 | script | `plan.json` | `script.json` | LLM |
| G1 | script gate | `script.json` | `qa/script.json` | 없음 |
| S3 | images | `script.json` | `images/scene-NN.png` + `images/index.json` | 이미지 생성 |
| G2 | image gate | `images/` | `qa/images.json` | (선택) 비전 LLM |
| S4 | voice | `script.json` | `audio/voice/scene-NN.wav` + `audio/voice/index.json` (실측 길이) | TTS |
| S5 | timeline | `script.json`, voice index | `timeline.json` (장면 시작/끝, 자막 타이밍) | 없음 |
| S6 | audio mix | timeline, voice, BGM, SFX | `audio/mix.wav` | 음원 라이브러리 |
| S7 | render | timeline, images, mix | `render/final.mp4` | ffmpeg (로컬) |
| S8 | cover | `script.json`, 이미지 | `render/cover.jpg` | 없음 |
| G3 | video gate | `final.mp4` | `qa/video.json` | ffprobe (로컬) |
| P1 | publish youtube | 완성본, `script.upload` | `publish/youtube.json` (영수증) | YouTube API |
| P2 | publish instagram | 완성본, `script.upload` | `publish/instagram.json` (영수증) | Instagram Graph API |

게이트는 일반 스테이지와 같은 인터페이스를 쓰되, 실패 시 **이전 생성 스테이지를 재생성**시킨다 (§5.2).

## 4. 런 상태와 매니페스트

### 4.1 런 디렉터리

```
runs/{run_id}/
  manifest.json          # 런 상태의 단일 진실 원천 (schemas/manifest.schema.json)
  plan.json
  script.json
  images/ scene-01.png … index.json
  audio/  voice/… mix.wav
  timeline.json
  render/ final.mp4 cover.jpg
  qa/     script.json images.json video.json
  publish/ youtube.json instagram.json
  logs.jsonl             # 구조화 로그
```

`run_id` 형식: `YYYYMMDD-HHMM-{era}-{rand4}` (예: `20261123-0310-2000s-k7q2`). 제작 시각 기준이며 슬롯과는 게시 시점에 연결된다.

### 4.2 런 상태 머신

```
 created → producing → ready ──(review 모드)──▶ awaiting_approval → ready
                │                                          │
                ▼                                          ▼ (거절)
             failed                                     rejected
 ready → publishing → published        (플랫폼 하나만 성공하면 partially_published)
```

- `ready`인 런이 게시 버퍼다. publish 잡은 가장 오래된 `ready` 런을 집는다 (FIFO, 같은 시대 연속 회피 옵션).
- 런 상태 전이는 매니페스트에만 기록되며, 매니페스트 쓰기도 원자적이다.

### 4.3 스테이지 상태

각 스테이지는 매니페스트에 다음을 남긴다.

```
pending → running → succeeded
                 ↘ failed (attempts, error.class, error.message)
         skipped (입력 해시 일치로 재사용)
```

`input_hash` = 해당 스테이지 입력 파일들의 SHA-256 + 스테이지 버전 + 관련 설정값.
재실행 시 `succeeded` 이고 `input_hash`가 같고 출력 파일이 존재·검증되면 `skipped` 처리한다.
상류 스테이지 출력이 바뀌면 해시가 달라지므로 하류는 자동으로 다시 돈다.

## 5. 장애 처리

### 5.1 오류 분류

| 클래스 | 예 | 처리 |
|---|---|---|
| `TransientError` | 네트워크 끊김, 타임아웃, HTTP 429/5xx | 지수 백오프 + 지터로 재시도 (기본 5회, 2s→60s). `Retry-After` 존중 |
| `ProviderError` | 공급자 장애가 재시도 한도를 넘김, 서킷 오픈 | 폴백 체인의 다음 공급자로 전환 |
| `QualityError` | 게이트 불합격 (자막 너무 김, 길이 초과, 얼굴 왜곡 등) | 해당 생성 스테이지를 피드백과 함께 재생성 (기본 3회) |
| `ValidationError` | 스키마 불일치 (LLM이 JSON 깨뜨림 등) | 재생성으로 취급 (QualityError와 같음) |
| `BudgetError` | 편당 비용 상한 초과 | 런 중단, 알림 |
| `FatalError` | 인증 실패, 설정 오류, 쿼터 소진, 정책 위반 | 즉시 중단, 알림. 자동 재시도 금지 |

### 5.2 재생성 루프

```
for attempt in 1..max_regen:
    out = 생성 스테이지(input, feedback)
    report = 게이트(out)
    if report.passed: break
    feedback = report.issues   # 다음 생성 프롬프트에 그대로 넣는다
else:
    런 failed (QualityError) + 알림
```

이미지는 장면 단위로 재생성한다 (6장 중 1장만 불합격이면 그 1장만).

### 5.3 서킷 브레이커와 폴백

공급자별로 최근 연속 실패 수를 센다. 임계치(기본 3)를 넘으면 일정 시간(기본 10분) 해당 공급자를 건너뛰고 폴백 체인의 다음 공급자를 쓴다. 폴백이 없으면 `ProviderError`로 런 실패.

### 5.4 게시 멱등성 (중복 업로드 방지)

```
key = "{run_id}:{platform}"
1. publish/{platform}.json 에 status=published 있으면 → 끝 (이미 게시)
2. publisher.find_existing(key) → 있으면 영수증 기록 후 끝
     (유튜브: 업로드 시 영상 태그에 `rrs-{run_id}`를 넣고, 채널 최근 업로드에서 그 태그를 조회
      인스타: 컨테이너 ID를 게시 전에 영수증에 기록해 두고, 그 컨테이너의 상태(PUBLISHED 여부)를 조회)
3. 업로드 전 publish/{platform}.json 에 status=uploading, started_at 기록
4. 업로드 → 플랫폼 ID 받으면 즉시 status=published, platform_id 기록
```

3단계 이후 죽었다면 재실행 시 2단계 조회로 회복한다. 조회로도 판단이 안 되면 **다시 올리지 않고** 사람에게 확인을 요청한다 (중복 게시보다 누락이 낫다).

### 5.5 동시 실행 방지

- GitHub Actions `concurrency` 그룹으로 produce 잡, publish 잡 각각 동시 1개.
- 런 디렉터리에 `lock` 파일(호스트, PID, 시작 시각). 오래된 락(기본 2시간)은 회수.

### 5.6 슬롯 보장 (버퍼)

- `buffer.target` (기본 3): produce 잡은 `ready` 런 수가 이보다 적을 때만 새로 만든다.
- `buffer.min` (기본 1): 이 아래로 떨어지면 경고 알림.
- 슬롯에 `ready` 런이 하나도 없으면 그 슬롯은 건너뛰고 즉시 알림 (엉터리 영상을 급조하지 않는다).

## 6. 설정

```
config/
  pipeline.yaml    # 공급자 선택·폴백 순서, 재시도·재생성 횟수, 예산, 승인 모드, 버퍼
  schedule.yaml    # 게시 슬롯 (시간대 포함), produce 주기
  eras.yaml        # 시대별 비주얼 스타일 기본값, 소품, 금지 시대착오 목록
  banned.yaml      # 금칙어 (실존 노래·가수·상표 등)
```

설정은 시작 시 스키마로 검증하고, 잘못되면 `FatalError`로 아무 것도 하지 않고 멈춘다.

## 7. 관측성

- **로그**: `logs.jsonl` 한 줄 = `{ts, run_id, stage, level, event, attempt, provider, duration_ms, cost_usd, msg}`. 비밀값은 마스킹 필터 통과 후 기록.
- **비용**: 어댑터가 호출마다 추정 비용을 반환하고 매니페스트에 누적.
- **알림**: 런 실패(원인 + 재실행 명령), 게시 성공(링크), 승인 요청(review 모드), 버퍼 부족, 토큰 만료 임박(7일 전).
- **보존**: 런 디렉터리는 게시 후 30일 보관. 완성본과 매니페스트는 오브젝트 스토리지에 영구 보관.

## 8. 실행 환경 (가정: GitHub Actions)

| 잡 | 트리거 | 내용 |
|---|---|---|
| `produce` | cron (예: 매일 03:00 KST) + 수동 | 버퍼 채우기. 런 디렉터리를 오브젝트 스토리지에 동기화 |
| `publish` | cron (슬롯 시각) + 수동 | 가장 오래된 `ready` 런 게시 |
| `ci` | PR | 린트, 타입 체크, 단위 테스트, 스키마 검증, 샘플 대본으로 S5~G3 드라이런 (공급자 모킹) |
| `token-check` | 매일 | 토큰 만료 임박 알림 |

GitHub Actions cron은 수 분~수십 분 지연될 수 있으므로, publish 잡은 슬롯 30분 전에 시작해 슬롯 시각까지 대기 후 게시하거나, 플랫폼 예약 게시 기능(유튜브 `publishAt`)을 사용한다.

## 9. 코드 구조 (예정)

```
pipeline/
  cli.py                 # rrs produce | publish | run --from STAGE | validate
  core/
    stage.py             # Stage 프로토콜, StageResult
    runner.py            # 스테이지 순서 실행, 스킵·재시도·재생성·상태 기록
    manifest.py          # 원자적 읽기/쓰기, 상태 전이 검증
    errors.py            # 오류 클래스 계층
    retry.py             # 백오프, 서킷 브레이커
    io.py                # 원자적 파일 쓰기, 해시
  stages/                # S1~S8, G1~G3, P1~P2 (스테이지당 파일 1개)
  providers/
    base.py              # LLM/Image/TTS/Music/Publisher 프로토콜
    llm_anthropic.py  image_*.py  tts_*.py  youtube.py  instagram.py
    fake.py              # 테스트용 가짜 공급자 (결정적 출력)
schemas/                 # JSON 스키마 (계약의 원본)
tests/
```

언어: Python 3.12, 렌더링: ffmpeg. 스키마 검증: `jsonschema`.

## 10. 확장 지점

- 정지 이미지 대신 이미지→영상 모델로 장면별 3~5초 클립 생성 (S3 뒤에 S3b 추가, 렌더 입력만 바뀜)
- 다른 플랫폼(틱톡) 게시 = Publisher 어댑터 1개 추가
- 성과 수집(조회수) 스테이지를 추가해 S1 plan의 테마 선택에 반영
