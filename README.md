# 우리가 열여덟이던 겨울 · AI 연재 숏드라마 스튜디오

> 2006년 겨울, 한국의 한 고등학교. 전학 첫날 학교 최고 인기남이 내 폴더폰을 박살 냈다.

2000년대 한국 고교 로맨스를 **세로 1분 연재 숏드라마**로 만드는 제작 파이프라인입니다.
배우 얼굴을 고정한 실사 스틸 → 실제로 움직이는 컷 → 감정 연기 목소리·장면별 음악·효과음·자막 → 완성본까지,
**유료 API 없이 무료 도구만으로** 만듭니다. 유튜브 쇼츠·인스타 릴스에 EP.01부터 순서대로 올리는 것이 목표입니다.

| | |
|---|---|
| 형식 | 9:16 세로, 화당 60초 안팎, 2~3초 컷, 첫 3초 훅, 끝 2~4초 떡밥 |
| 주인공 | 윤서진(여주, 전학생) · 강도윤(남주, 학교 최고 인기남), 화마다 같은 얼굴 |
| 비용 | 0원 (무료 GPU 할당량, 무료 CPU, 무료 음성) |
| 상태 | EP.01 9컷 중 4컷 완성, 편집기·음악·자막 완성, 남은 컷 생성 중 |

## 한 화가 만들어지는 과정

```
배우 얼굴 사진 (cast)
   │  Qwen-Image-Edit-2509 / SDXL + IP-Adapter Face  ← 같은 얼굴, 장면·교복·배경만 바꿈
   ▼
컷 스틸 (720×1280)
   │  Wan 2.2 이미지→영상 (A14B 가속판 / TI2V-5B / FastWan 3스텝)
   ▼
움직이는 컷 3~5초 (16fps)
   │  Real-ESRGAN 4배 업스케일 + GFPGAN 얼굴 복원 (CPU)
   ▼
고화질 컷
   │  pipeline/episode/edit.py
   │   - 움직임 보간 30fps, 컷마다 카메라 밀기, 충격 순간 흔들림·번쩍
   │   - Gemini TTS 인물별 목소리 + 감정 태그([annoyed], [whispering] …)
   │   - 장면별 음악 큐(긴장·밀당·설렘) 코드 합성, 효과음 합성, -14 LUFS
   │   - 첫 3초 훅 문구, 인물 색 자막(팝업), 폴더폰 문자 화면, 다음 화 예고
   ▼
final.mp4 (1080×1920, 30fps)
```

## 무료 GPU를 어떻게 쓰나

| 경로 | 워크플로 | 쓰는 곳 | 비고 |
|---|---|---|---|
| Hugging Face Spaces (ZeroGPU) | `space-episode.yml` | 스틸 + 영상 | 가장 빠름(컷당 1분), 하루 무료 한도 있음 (`HF_TOKEN`) |
| Kaggle CPU | `kaggle-clips.yml` + `jobs/cpu-*.json` | 스틸 + 영상 | 느리지만 완전 무료, 4코어·31GB, 12시간 |
| Kaggle GPU (T4) | `kaggle-clips.yml` | 영상·스틸 | 계정 대기열 문제로 현재 대기 중 |
| Modal | `modal-episode.yml` | 스틸 + 영상 (H100/L40S) | 월 $30 크레딧이지만 GPU 쓰려면 카드 등록 필요 → 미사용 |
| GitHub Actions CPU | `enhance-clips.yml` | 업스케일·얼굴 복원 | 무료 |

모든 작업은 **해당 JSON을 push하면** 돌고, 결과는 `experiment-output` 브랜치 `runs/<종류>-<run_id>/`에 올라옵니다.

```bash
# 컷 만들기 (HF Space)      pipeline/experiments/space-jobs/ep01.json 수정 후 push
# 컷 만들기 (Kaggle CPU)    pipeline/kaggle/jobs/cpu-<이름>.json 추가 후 push
# 화질 올리기              pipeline/experiments/enhance-jobs/<이름>.json 추가 후 push
# 한 화 편집 (로컬)
export GEMINI_API_KEY=...   # 무료 등급
python -m pipeline.episode.edit episodes/ep01/edit.json out/ep01
```

## 사용 모델과 라이선스 (상업 이용 가능한 것만)

| 용도 | 모델 | 라이선스 |
|---|---|---|
| 영상 | Wan 2.2 (TI2V-5B, I2V-A14B), FastWan2.2 | Apache-2.0 |
| 스틸·얼굴 유지 | Qwen-Image-Edit-2509, RealVisXL V5.0 + IP-Adapter Plus Face | Apache-2.0 / OpenRAIL++ |
| 업스케일·얼굴 | Real-ESRGAN, GFPGAN v1.4 | BSD-3 / Apache-2.0 |
| 음성 | Gemini TTS 무료 등급 | Google 약관 |
| 음악·효과음 | 코드로 직접 합성 (`pipeline/episode/score.py`, `sfx.py`) | 자체 제작 |
| 폰트 | 나눔스퀘어·나눔고딕 | OFL |

제외: CodeFormer(비상업), insightface 계열(InstantID 등, 비상업), HunyuanVideo(한국 제외 라이선스).

## 폴더

```
episodes/ep01/edit.json      1화 편집 대본: 컷·대사·감정·효과음·음악 큐·훅
pipeline/episode/            편집기(edit.py), 음악 큐(score.py), 효과음(sfx.py)
pipeline/experiments/        HF Space·Modal 실행기, 화질 올리기
pipeline/kaggle/             Kaggle GPU/CPU 커널과 실행기
.github/workflows/           위 작업들을 push로 돌리는 워크플로
docs/ schemas/               초기 설계 문서와 계약 스키마
```

## 원칙

- 모든 이야기·인물·대사는 오리지널. 분위기만 참고합니다.
- 인물은 고등학생 설정이지만 풋풋한 로맨스만 다룹니다. 이미지는 20대 초반 배우가 교복을 입은 느낌으로 만듭니다.
- 업로드는 사람이 완성본을 보고 허락한 뒤에만 합니다. 실사형 AI 영상이라 합성 콘텐츠 라벨을 붙입니다.
- API 키와 토큰은 GitHub Actions 시크릿에만 둡니다.
