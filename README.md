# 손그림 쇼츠 공방 · Claude가 직접 그리는 세로 쇼츠

> AI 그림 생성기 대신, 장면 하나하나를 코드(SVG)로 직접 그려서 움직이는 1분 쇼츠를 만듭니다.

**방향 (2026-11-24 확정): 손그림 베이스.** 같은 대본으로 3D 화풍 AI 그림판과 손그림판을 만들어 비교한 뒤, 손그림을 기본으로 정했습니다.
채널 포맷은 고르는 중입니다. 이미 많은 채널이 하는 "만약에 ~라면 1년·5년·10년 뒤"를 그대로 따라 하지 않고, 이 채널만의 포맷을 찾습니다.

**유료 API 없이 무료 도구만** 씁니다.

| | |
|---|---|
| 형식 | 세로 1080×1920, 60~80초, 2~4초마다 컷 |
| 그림 | Claude가 SVG로 직접 그린 장면·캐릭터 (명암·그림자·조명), 카메라가 장면 안을 줌·이동하며 컷을 나눔 |
| 연출 | 큰 자막(핵심 단어 노랑 강조), 첫 3초 질문, 단계 도장, 끝 질문 카드 |
| 소리 | 내레이터·인물 목소리(Supertonic 3, 무료·CPU), 강아지 등은 음높이를 올린 귀여운 톤, 코드로 합성한 음악·효과음 |
| 비용 | 0원 (그림·렌더는 이 컨테이너, 목소리는 GitHub Actions 무료 러너) |
| 상태 | 시범작 "만약 강아지가 말을 한다면?" (콩이와 누나의 10년) 완성 → 채널 포맷 선정 중 |

## 한 편이 만들어지는 과정

```
대본 (pipeline/whatif/<id>.json)
   │  컷마다: 어느 장면 · 카메라 위치(cam → cam2) · 단계("1년 뒤") · 한 줄 대사(who, text, *강조*)
   ▼
목소리 (.github/workflows/saeyeon-voices.yml, Supertonic 3)
   │  대본을 push 하면 러너가 만들어 experiment-output 브랜치 runs/voices-<run>/ 에 올림
   ▼
타임라인·소리 (pipeline/whatif/make.py)
   │  대사 길이로 컷 시간 결정, 자막을 2~4어절씩 쪼갬, 밝은 음악 + 컷 효과음 + 단계 띵 소리, 대사 중 음악 낮춤
   ▼
그림 (pipeline/whatif/art.js + punch.html)
   │  window.render(t)로 매 프레임을 그림 → Playwright로 30fps 촬영 (4개 동시)
   ▼
완성 영상 (1080×1920, -14 LUFS) + 휴대폰용 720p 미리보기
```

```bash
python pipeline/whatif/make.py pipeline/whatif/w01-dog.json <작업폴더> --fake-tts --no-render   # 길이·자막만 확인
python pipeline/whatif/make.py pipeline/whatif/w01-dog.json <작업폴더> --jobs 4                # <작업폴더>/voice 에 목소리를 넣은 뒤
```

## 그림 라이브러리 (pipeline/whatif/art.js)

- 캐릭터: `dog2()` 시바견 (나이 든 모습·안경·조끼·넥타이·헤드셋·눈물 옵션, 말할 때 입·꼬리·눈 깜빡임), `human()` 사람 (놀람·떨어뜨림·안기 포즈, 표정·눈물), 고양이
- 장면 11개: 침실, 부엌, 뉴스 스튜디오, 소파(밤·우는 사람), 공항 검색대, 눈 덮인 산, 교실, 네온 거리, 방송방, 투표소, 노을 진 마루
- 배경을 넓게 그려서 세로 카메라가 어디를 잘라도 비지 않음

## 수익 정지를 피하는 규칙 (유튜브 2026-07-16 정책)

- 사진 넘기기 슬라이드쇼·템플릿 양산 금지: 장면은 직접 그리고, 편마다 새 장면·새 이야기를 만듭니다.
- 감정을 쥐어짜는 막장·불행 전시 금지, 건강·돈·법·정치 조언 금지.
- 모든 이야기·캐릭터는 새로 만든 창작물이며, 설명란에 창작·합성 콘텐츠 표시를 붙입니다.
- 업로드는 사람이 완성본을 보고 허락한 뒤에만 합니다.

## 사용 도구와 라이선스

| 용도 | 도구 | 라이선스 |
|---|---|---|
| 그림·움직임 | SVG를 Claude가 직접 작성, Playwright(Chromium)로 프레임 렌더 | 자체 제작 / Apache-2.0 |
| 목소리 | Supertonic 3 (Supertone) | 코드 MIT, 모델 OpenRAIL-M |
| 음악·효과음 | numpy로 직접 합성 (pipeline/episode/score.py 악기) | 자체 제작 |
| 폰트 | 나눔스퀘어·나눔고딕·나눔명조 | OFL |
| 영상 합성 | ffmpeg | LGPL |

## 폴더

```
pipeline/whatif/     지금 쓰는 쇼츠 제작기 (art.js 그림, punch.html 화면, make.py 조립)
pipeline/saeyeon/    이전 실험: 5070 사연 낭독(느린 우체통) 엔진과 장면 13개, 목소리 생성기
pipeline/episode/    음악 악기(score.py)·효과음
assets/fonts/        나눔 폰트
```

## 이전 실험

- **3D 화풍 AI 그림판**: DreamShaper XL Lightning을 GitHub Actions CPU 8대로 돌려 그림 21장 생성 (`.github/workflows/whatif-images.yml`, `pipeline/whatif/gen_images.py`). 품질은 좋았지만 손그림 베이스로 결정.
- **느린 우체통 (5070 사연 낭독)**: `pipeline/saeyeon/`
- **학원 로맨스 숏드라마 "우리가 열여덟이던 겨울"**: 실사형 AI 영상(Wan 2.2), 얼굴 고정(Qwen-Image-Edit), 화질 올리기, 입 모양 맞추기(MuseTalk). `pipeline/experiments/`, `pipeline/kaggle/`, `episodes/`

## 원칙

- 모든 이야기·인물·대사는 오리지널입니다.
- API 키와 토큰은 GitHub Actions 시크릿에만 둡니다.
