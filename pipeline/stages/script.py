"""S1 plan + S2 script + G1 script gate.

무료 Gemini 텍스트 모델로 2000년대 학창시절 테마 대본을 쓰고, 게이트에서 떨어지면 이슈를 피드백으로 넣어 다시 쓴다.
"""
import json
import random
import re
from pathlib import Path

import jsonschema
import yaml

from ..core.errors import QualityError, ValidationError
from ..core.io import read_json, write_json
from .common import KEY_RE
from .timeline import split_caption

BANNED = ["별이삼샵", "별이 삼샵", "연애혁명", "꽃보다남자", "꽃보다 남자", "F4", "구준표", "금잔디", "공주영", "왕자림",
          "싸이월드", "버디버디", "네이트온", "MSN", "애니콜", "롯데"]
SPEECH_RATE = 4.2      # 한국어 TTS 실측 초당 글자 수 (공백 제외, 2026-11-22 측정)


def plan(repo: Path, history: list[dict], seed: int) -> dict:
    cfg = yaml.safe_load((repo / "config" / "themes.yaml").read_text(encoding="utf-8"))
    recent = {h["topic"] for h in history[-12:]}
    pool = [t for t in cfg["topics"] if t not in recent] or cfg["topics"]
    return {"topic": random.Random(seed).choice(pool), "tone": cfg["tone"],
            "avoid_titles": [h["title"] for h in history[-30:]]}


def gate(script: dict, schema: dict) -> list[str]:
    issues = []
    try:
        jsonschema.validate(script, schema)
    except jsonschema.ValidationError as e:
        issues.append(f"SCHEMA_INVALID: {e.message} at {list(e.absolute_path)}")
        return issues
    sc = script["scenes"]
    total = sum(s["duration_sec"] for s in sc)
    if total != script["target_duration_sec"] or not 50 <= total <= 58:
        issues.append(f"DURATION_MISMATCH: 장면 길이 합 {total}초. target_duration_sec와 같고 50~58초여야 한다")
    if sc[0]["beat"] != "hook" or sc[-1]["beat"] != "ending":
        issues.append("BEAT_ORDER: 첫 장면은 hook, 마지막 장면은 ending")
    looks = {c["key"]: c["look"] for c in script["characters"]}
    for s in sc:
        for k in KEY_RE.findall(s["image_prompt"]):
            if not looks.get(k):
                issues.append(f"UNKNOWN_CHARACTER: scenes[{s['no']}] image_prompt의 {{{k}}}가 정의되지 않았거나 look이 비었다")
        for d in s["dialogue"]:
            if d["speaker"] not in looks:
                issues.append(f"UNKNOWN_CHARACTER: scenes[{s['no']}] speaker {d['speaker']}")
        chars = len(re.sub(r"\s", "", s["narration"] + "".join(d["line"] for d in s["dialogue"])))
        need = chars / SPEECH_RATE + 0.4 + 0.35 * len(s["dialogue"]) + 0.6
        if need > s["duration_sec"] + 1.5:
            issues.append(f"NARRATION_TOO_LONG: scenes[{s['no']}] 말이 {chars}자라 약 {need:.1f}초 걸린다. "
                          f"{s['duration_sec']}초 안에 들어가게 줄여라 (초당 약 {SPEECH_RATE}자)")
    blob = json.dumps(script, ensure_ascii=False)
    for b in BANNED:
        if b in blob:
            issues.append(f"BANNED_TERM: '{b}'는 실제 작품·상표라 쓰면 안 된다")
    return issues


SYSTEM = """너는 유튜브 쇼츠·인스타 릴스용 55초 세로 숏드라마 작가다.
조회수가 높은 감성 쇼츠처럼: 첫 2초에 공감 훅, 장면마다 한 가지 감정, 짧고 구어체인 문장, 마지막에 여운 한 줄.
반드시 주어진 JSON 형식과 똑같은 구조의 JSON 하나만 출력한다. 설명 문장 금지."""


def build_prompt(p: dict, example: dict, schema: dict, feedback: list[str] | None) -> str:
    ex = json.loads(json.dumps(example))
    for c in ex["characters"]:  # 나이 숫자는 안전 필터를 불필요하게 자극하므로 예시에서 뺀다
        c["look"] = re.sub(r",?\s*\d+\s*years? old( in \d{4})?( then \d+)?", "", c["look"])
    s = f"""테마 톤: {p['tone']}
이번 소재: {p['topic']}
최근에 쓴 제목(겹치지 않게): {', '.join(p['avoid_titles']) or '없음'}

규칙:
- era는 "2000s". id는 "2000s-900"(파이프라인이 바꾼다). schema_version "1.0.0". aspect_ratio "9:16".
- 아래 JSON 스키마의 길이 제한(maxLength 등)을 반드시 지킨다.
- 장면 5~7개. beat 순서는 hook, memory, (memory/conflict), turn, ending. 장면 길이 합 = target_duration_sec(52~56).
- 내레이션은 30대가 된 주인공의 담담한 회상(1인칭). 대사는 짧게. 한 장면 말은 (장면 초 × 4)자 이하.
- 로맨스는 순수한 설렘(눈 마주침, 쪽지, 우산 같이 쓰기 정도)까지만. 신체 접촉·외모의 성적 묘사·키스는 절대 쓰지 않는다.
  학생 인물의 외모는 교복과 머리 모양만 묘사하고 나이 숫자는 쓰지 않는다(예: "middle school student").
- 실제 작품명·캐릭터·연예인·노래 제목·상표(싸이월드, 버디버디 등 서비스명 포함)는 쓰지 않는다. '빼빼로데이' 같은 기념일 이름은 써도 된다.
- 등장인물은 2~3명. characters[].look은 영어로, 실사 사진 생성용 외모 묘사(나이, 교복/옷, 머리 모양)를 구체적으로.
  어린 시절과 커서의 모습이 다르면 look에 둘 다 적는다. voice는 "수줍은 10대 남성"처럼 성별과 나이대를 꼭 넣는다.
  화면에만 나오고 말하지 않는 인물은 voice를 "대사 없음"으로.
- image_prompt는 영어, 실사 영화 스틸 사진 묘사. 인물은 {{A}} 같은 키로만 부른다. 2000년대 소품(폴더폰, MP3, 교복, 문방구 등) 구체적으로.
- motion_prompt는 카메라 움직임 한 줄(slow push in 등).
- captions는 비워도 된다(파이프라인이 다시 만든다). upload.yt_title에는 #shorts 포함, hashtags 4~6개.

JSON 스키마:
{json.dumps(schema, ensure_ascii=False)}

출력 예시(형식 참고용, 내용은 새로 쓸 것):
{json.dumps(ex, ensure_ascii=False)}
"""
    if feedback:
        s += "\n이전 원고의 문제점(반드시 고칠 것):\n- " + "\n- ".join(feedback)
    return s


def run(repo: Path, llm, history: list[dict], seed: int, out: Path, log=print, max_regen: int = 3) -> tuple[dict, str]:
    schema = read_json(repo / "schemas" / "script.schema.json")
    example = read_json(repo / "scripts" / "samples" / "2000s-003.json")
    p = plan(repo, history, seed)
    log(f"[plan] 소재: {p['topic']}")
    feedback = None
    for attempt in range(1, max_regen + 2):
        try:
            (script, _), prov = llm.call("complete_json", SYSTEM, build_prompt(p, example, schema, feedback), None,
                                         16384, seed + attempt)
        except ValidationError as e:
            log(f"[script] {attempt}차 응답이 JSON이 아님: {str(e)[:200]}")
            if "blockReason" in str(e):  # 안전 필터에 막히면 소재를 바꿔 다시 기획한다
                p = plan(repo, history + [{"topic": p["topic"], "title": ""}], seed + attempt * 7)
                log(f"[plan] 필터에 막혀 소재 변경: {p['topic']}")
                feedback = None
            else:
                feedback = ["출력이 올바른 JSON이 아니었다. JSON 하나만, 끝까지 출력할 것"]
            continue
        script["id"] = f"2000s-{100 + len(history) % 900:03d}"
        for s in script.get("scenes", []):  # 자막은 파이프라인 규칙으로 다시 만든다
            text = " ".join([s.get("narration", "")] + [d.get("line", "") for d in s.get("dialogue", [])]).strip()
            s["captions"] = split_caption(text) or ["…"]
        issues = gate(script, schema)
        log(f"[script] {attempt}차 원고 ({prov}): {script.get('title')} → 이슈 {len(issues)}개")
        if not issues:
            write_json(out, script)
            return script, p["topic"]
        for i in issues:
            log(f"  - {i}")
        feedback = issues
    raise QualityError("SCRIPT_GATE", f"{max_regen + 1}번 써도 게이트를 못 넘었습니다: {feedback}")
