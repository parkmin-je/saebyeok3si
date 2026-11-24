# 느린 우체통 · 50~70대를 위한 사연 낭독 채널

> 지나간 시간에서 늦게 도착한 편지 한 통. 그 안에 담긴 인생 이야기를 천천히 읽어드립니다.

50~70대 시청자를 위한 **15~20분 사연 낭독 영상**을 만드는 제작 도구입니다.
이야기 파일 하나를 넣으면 대본 → 직접 그린 장면 → 내레이션·인물 목소리 → 음악·생활 소리 → 완성 영상까지 이어서 만듭니다.
**유료 API 없이 무료 도구만** 씁니다.

| | |
|---|---|
| 형식 | 16:9 가로, 15~20분, 사연 3~4개를 한 주제로 묶음, 주 2회 |
| 시청자 | 50~70대: 틀어두고 듣고, TV·폰으로 멀리서 봄 |
| 화면 | 사진 대신 장면을 코드로 직접 그림(HTML/SVG), 천천히 움직이는 카메라, 58px 이상 큰 자막 |
| 소리 | 내레이터 1명 고정 + 인물별 목소리(Gemini TTS 무료), 코드로 합성한 장조 음악, 대사 중 음악 자동 낮춤 |
| 비용 | 0원 |
| 상태 | 1분 시범 완성 → 장면 라이브러리·1화 20분 제작 중 |

설계서: [느린 우체통 · 5070 사연 채널 설계서](https://claude.ai/artifact/VSVM145um2WAEKMSbP2b4B)

## 한 편이 만들어지는 과정

```
이야기 파일 (pipeline/saeyeon/epNNN/lines.json)
   │  사연 3~4개, 대사마다 누가·어떤 감정·어느 장면
   ▼
장면 (pipeline/saeyeon/story.html)
   │  장면 라이브러리에서 배경을 골라 시간대·계절·회상(세피아)을 바꿈
   │  window.render(t)로 매 순간을 그림 → Playwright가 30fps로 찍음 (render.js)
   ▼
목소리 (pipeline/saeyeon/tts.py)
   │  내레이터 Charon, 인물별 목소리, "[warm] 대사" 감정 태그, 만든 음성은 모두 보관
   ▼
음악·효과음 (pipeline/episode/score.py 의 악기)
   │  따뜻한 장조 피아노·패드, 회상은 낮고 먹먹하게, 시계·버스 같은 생활 소리
   ▼
완성 영상 (1920×1080, 30fps, -14 LUFS) + 휴대폰용 720p 미리보기
```

```bash
export GEMINI_API_KEY=...   # 무료 등급
python pipeline/saeyeon/tts.py <작업폴더>        # lines.json → voice/*.wav
node pipeline/saeyeon/render.js <작업폴더> full  # story.html → frames/*.jpg
```

## 수익 정지를 피하는 규칙 (유튜브 2026-07-16 정책)

- 사진 넘기기 슬라이드쇼 금지: 장면은 직접 그리고 움직이며, 편마다 새 장면을 2개 이상 추가합니다.
- 감정을 쥐어짜는 막장·불행 전시 금지: 따뜻한 반전과 작은 깨달음으로 끝냅니다.
- 건강·노후 자금·상속·정치 조언은 다루지 않습니다.
- 모든 이야기는 새로 쓴 창작물이며, 설명란에 "실화가 아닌 창작 이야기", 합성 콘텐츠 표시를 붙입니다.
- 업로드는 사람이 완성본을 보고 허락한 뒤에만 합니다.

## 사용 도구와 라이선스

| 용도 | 도구 | 라이선스 |
|---|---|---|
| 장면 그림·움직임 | HTML/SVG를 Claude가 직접 작성, Playwright(Chromium)로 프레임 렌더 | 자체 제작 / Apache-2.0 |
| 목소리 | Gemini TTS 무료 등급 | Google 약관 |
| 음악·효과음 | numpy로 직접 합성 | 자체 제작 |
| 폰트 | 나눔명조·나눔고딕 | OFL |
| 영상 합성 | ffmpeg | LGPL |

## 폴더

```
pipeline/saeyeon/        사연 채널 제작기 (장면 HTML, 렌더러, 목소리)
pipeline/saeyeon/ep001/  1분 시범 "아버지의 시계는 왜 늘 5분 빨랐을까"
pipeline/episode/        음악 악기(score.py)·효과음(sfx.py), 이전 실험의 편집기
assets/fonts/            나눔 폰트
```

## 이전 실험: 학원 로맨스 숏드라마

처음에는 2000년대 학원 로맨스 세로 숏드라마("우리가 열여덟이던 겨울")를 만들었습니다.
실사형 AI 영상(Wan 2.2), 얼굴 고정(Qwen-Image-Edit), 화질 올리기(Real-ESRGAN·GFPGAN), 입 모양 맞추기(MuseTalk) 같은 도구는
`pipeline/experiments/`, `pipeline/kaggle/`, `.github/workflows/`, `episodes/`에 그대로 남겨 두었습니다. 필요하면 사연 채널의 쇼츠나 재연 장면에 다시 씁니다.

## 원칙

- 모든 이야기·인물·대사는 오리지널입니다.
- API 키와 토큰은 GitHub Actions 시크릿에만 둡니다.
