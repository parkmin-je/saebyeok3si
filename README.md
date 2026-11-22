# retro-romance-shorts

1900년대·2000년대의 로맨스, 추억, 그리움을 테마로 한 50~58초 세로 숏드라마를 AI로 자동 제작하고,
정해진 시간에 유튜브 쇼츠와 인스타그램 릴스로 자동 게시하는 파이프라인입니다.

## 문서

| 문서 | 내용 |
|---|---|
| [요구사항 명세서](docs/REQUIREMENTS.md) | 기능·비기능 요구사항, "깨지지 않는다"의 정의, 플랫폼 제약, 미정 사항 |
| [아키텍처 설계서](docs/ARCHITECTURE.md) | 스테이지 구성, 런 상태 머신, 장애 처리, 게시 멱등성, 실행 환경 |
| [인터페이스 명세서](docs/INTERFACES.md) | 스테이지·게이트·공급자 어댑터 인터페이스, 파일 계약, CLI, 환경 변수 |
| [`schemas/`](schemas/) | 계약의 원본 JSON 스키마 (대본, 타임라인, 매니페스트, 게시 영수증) |

## 한눈에 보는 구조

```
[produce 잡]  plan → script → (게이트) → images → (게이트) → voice → timeline
              → audio mix → render → cover → (게이트) → 버퍼에 ready
[publish 잡]  슬롯 시각에 버퍼에서 1편 → YouTube 쇼츠 / Instagram 릴스 (각각 독립, 중복 게시 방지)
```

깨지지 않게 만드는 핵심 장치:

- **제작과 게시 분리**: 완성본을 2~3편 미리 쌓아 두고 정시에 게시하므로, 제작이 실패해도 슬롯을 놓치지 않습니다.
- **파일 계약 + 스키마 검증**: 스테이지는 검증된 파일로만 주고받습니다.
- **멱등·재개 가능**: 입력 해시가 같은 스테이지는 건너뛰고, 실패 지점부터 다시 돕니다.
- **오류 분류**: 일시 오류는 재시도, 품질 불합격은 피드백을 넣어 재생성, 인증·설정 오류는 즉시 중단·알림.
- **공급자 폴백 + 서킷 브레이커**: 이미지/TTS 공급자 하나가 죽어도 다음 공급자로 이어갑니다.
- **게시는 정확히 한 번**: 멱등 키와 영수증으로 중복 업로드를 막습니다.

## 샘플 영상 만들기 (무료 방식)

```bash
pip install -r requirements.txt          # ffmpeg, Node.js + Playwright(Chromium)도 필요
export GEMINI_API_KEY=...                # 무료 등급 키 (음성용)
python -m pipeline.cli produce --script scripts/samples/1930s-001.json
# → runs/<run_id>/render/final.mp4, cover.jpg, qa/video.json
python -m pipeline.cli produce --script scripts/samples/1930s-001.json --fake   # 외부 호출 없는 드라이런
```

그림은 `pipeline/illustrated/<대본 id>.html`에 Claude가 직접 그린 장면이고, 프레임마다 `render(t)`로 그려
1080×1920·30fps로 찍습니다. 음성은 Gemini TTS 무료 등급, 배경음악은 코드로 합성한 피아노 왈츠,
자막은 나눔명조(OFL)로 입힙니다. 지금은 `1930s-001` 장면 파일만 있습니다.

## 폴더 구조

```
docs/             요구사항·아키텍처·인터페이스 문서
schemas/          JSON 스키마 (계약의 원본)
scripts/samples/  샘플 대본 4편 (스키마 통과)
pipeline/         파이프라인 코드 (구현 예정, 구조는 ARCHITECTURE.md §9)
config/           파이프라인·스케줄·시대·금칙어 설정
assets/           음원 라이브러리 등 (생성물은 git 제외)
output/           로컬 출력 (git 제외)
```

## 보안

API 키와 계정 토큰은 `.env` 또는 GitHub Actions 시크릿에만 둡니다. `.env.example`을 참고하세요.
