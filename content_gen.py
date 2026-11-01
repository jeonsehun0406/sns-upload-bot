"""
콘텐츠 생성 모듈 - 요일별 다양한 타입 (크롤링 없음)
Gemini가 직접 주제를 창작하여 안정적으로 콘텐츠 생성
"""

import json
import random
from datetime import datetime
from pathlib import Path
from config import GEMINI_API_KEY, APP_NAME, TOPIC_POOL

_USED_FILE = Path(__file__).parent / "used_topics.json"

def _load_used() -> dict:
    if _USED_FILE.exists():
        try:
            return json.loads(_USED_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _save_used(data: dict):
    _USED_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _pick(pool: list, type_key: str) -> str:
    used      = _load_used()
    used_list = used.get(type_key, [])
    available = [x for x in pool if x not in used_list]
    if not available:
        print(f"[content_gen] '{type_key}' 소재 소진 → 리셋")
        used_list = []
        available = list(pool)
    chosen = random.choice(available)
    used_list.append(chosen)
    used[type_key] = used_list
    _save_used(used)
    print(f"[content_gen] [{type_key}] 선택: {chosen}  (사용됨: {len(used_list)}/{len(pool)})")
    return chosen

GEMINI_MODEL = "gemini-3.8-flash"

CONTENT_SCHEDULE = {
    0: "사주_상식",
    1: "궁합",
    2: "관계_갈등",
    3: "심리_퀴즈",
    4: "관계_갈등",
    5: "일주_특징",
    6: "오늘의운세",
}
DOW_KR = ["월", "화", "수", "목", "금", "토", "일"]

_JSON_FORMAT = """\
아래 JSON으로만 출력. 마크다운 코드블록 없이 순수 JSON만:
{
  "display_title": "25자 이내 바이럴 제목. 반드시 훅 사용",
  "category": "카테고리명",
  "slides": [
    "슬라이드 1 (160~220자) — 첫 문장은 반드시 충격·공감·강렬한 질문 중 하나로 시작. 2~3문장마다 \\n 줄바꿈 필수",
    "슬라이드 2 (160~220자, \\n 줄바꿈 필수)",
    "슬라이드 3 (160~220자, \\n 줄바꿈 필수)",
    "슬라이드 4 (160~220자, \\n 줄바꿈 필수)"
  ],
  "side_a": "한쪽 의견 (8자 이내)",
  "side_b": "반대 의견 (8자 이내)",
  "engagement_q": "참여 유도 질문 (20자 이내)",
  "promo_hook": "공감 후 운명의문 자연 연결 훅 (22자 이내, 광고티 없이)",
  "image_prompt": "fal.ai용 영어 배경 이미지 프롬프트 (no text no people, 30단어 이내)",
  "caption": "인스타 캡션 이모지 풍부 100자 이내",
  "hashtags": "#사주 #운명의문 #오늘의운세 #심리 #연애 #공감 #인간관계 #운세 #심리테스트 #사주팔자"
}"""


def _get_client():
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def _call_gemini(prompt: str) -> dict:
    client   = _get_client()
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    raw      = response.text.strip()
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break
    return json.loads(raw.strip())


_SAJU_TOPICS = [
    "일주(日柱)", "십신(十神)", "오행(五行)의 상생상극", "용신(用神)",
    "대운(大運)의 흐름", "천간(天干) 10개", "지지(地支) 12개",
    "갑자일주의 특징", "병화 일간의 성격", "경금 일간의 특징",
    "공망(空亡)이란?", "형충파해란?", "역마살이란?", "도화살이란?",
    "사주에서 보는 직업운", "사주에서 보는 재물운", "사주에서 보는 결혼운",
]

def _gen_saju_knowledge() -> dict:
    topic  = _pick(_SAJU_TOPICS, "사주_상식")
    prompt = f"""당신은 팔로워 50만 인스타그래머입니다. 사주를 전혀 모르는 일반인 독자를 대상으로 씁니다.
주제: {topic}
[훅 필수] 제목: "이거 모르면 손해", "알고 나면 소름", "사주에 이런 게?" 식의 강렬한 첫인상
[내용] 전문 용어 쓸 경우 바로 옆에 쉬운 말로 설명. 실생활 예시(연애, 직장). 2~3문장마다 \\n 줄바꿈.
{_JSON_FORMAT}"""
    result = _call_gemini(prompt)
    result["content_type"] = "사주_상식"
    return result


_GUNG_HAP_PAIRS = [
    "갑목×경금", "병화×임수", "무토×갑목", "경금×병화", "임수×무토",
    "을목×신금", "정화×계수", "기토×을목", "신금×정화", "계수×기토",
    "양띠×쥐띠", "호랑이띠×원숭이띠", "뱀띠×돼지띠",
]

def _gen_compatibility() -> dict:
    pair_str = _pick(_GUNG_HAP_PAIRS, "궁합")
    a, b = pair_str.split("×")
    prompt = f"""당신은 팔로워 50만 인스타그래머입니다. 사주를 모르는 일반인도 재미있게 읽을 수 있어야 합니다.
궁합 주제: {a} × {b}
[훅] 제목: "이 조합 실제로 폭발합니다" 식. {a}와 {b} 뜻 모르는 사람도 성격 특성으로만 설명.
슬라이드2: 환상 케미 순간. 슬라이드3: 폭발하는 순간. 슬라이드4: "내 궁합 궁금한 사람?" 2~3문장마다 \\n 줄바꿈.
{_JSON_FORMAT}"""
    result = _call_gemini(prompt)
    result["content_type"] = "궁합"
    return result


_CONFLICT_THEMES = [
    "결혼/이혼|결혼 후 드러나는 성격 차이",
    "연애/이별|연락 스타일이 너무 달라서 생기는 갈등",
    "시댁/처가|명절 문제로 시작된 부부 갈등",
    "직장/인간관계|직장에서 불합리한 대우를 당한 상황",
    "친구/우정|오래된 친구가 돈 문제로 달라진 경우",
    "연애/이별|썸 타다가 갑자기 잠수를 탄 상대방",
    "결혼/이혼|결혼 전에 몰랐던 상대방의 충격적인 모습",
    "가족/부모|부모님의 과한 간섭으로 힘든 상황",
    "연애/이별|장거리 연애의 현실적인 고충",
    "직장/인간관계|번아웃이 왔는데 아무도 몰라주는 상황",
]

def _gen_conflict_story() -> dict:
    theme = _pick(_CONFLICT_THEMES, "관계_갈등")
    category, situation = theme.split("|")
    prompt = f"""당신은 팔로워 50만 인스타그램 계정 운영자입니다.
오늘 주제: {situation} ({category})
[훅] 제목: "이거 읽다가 뜨끔한 사람?" 식. 슬라이드1 첫 문장: 감정을 확 건드리는 한 줄.
완전 창작이지만 "이거 나 얘기인가?" 싶을 만큼 공감되게. 2~3문장마다 \\n 줄바꿈.
{_JSON_FORMAT}"""
    result = _call_gemini(prompt)
    result["content_type"] = "관계_갈등"
    return result


_QUIZ_THEMES = [
    "상대방이 약속을 취소했을 때 나의 반응",
    "카톡 읽씹을 당했을 때 어떻게 하나요?",
    "싫어하는 사람과 같이 일해야 할 때",
    "연인과 여행 중 의견이 충돌할 때",
    "스트레스가 폭발 직전일 때 나의 해소법",
    "갑자기 혼자 시간이 생기면 뭘 하나요?",
    "직장 상사가 불합리한 요구를 할 때",
]

def _gen_psychology_quiz() -> dict:
    theme  = _pick(_QUIZ_THEMES, "심리_퀴즈")
    prompt = f"""당신은 사주/심리 전문 인스타그래머입니다.
퀴즈 주제: {theme}
[훅] 제목: "이거 선택하면 성격 다 나옴" 식. A타입 vs B타입 극명한 대비.
슬라이드2: A타입 반응. 슬라이드3: B타입 반응. side_a: "A타입이에요", side_b: "B타입이에요".
2~3문장마다 \\n 줄바꿈.
{_JSON_FORMAT}"""
    result = _call_gemini(prompt)
    result["content_type"] = "심리_퀴즈"
    return result


_ILJU_LIST = [
    "갑자", "갑인", "갑진", "갑오", "갑신", "갑술",
    "을축", "을묘", "을사", "을미", "을유", "을해",
    "병자", "병인", "병진", "병오", "병신", "병술",
    "정축", "정묘", "정사", "정미", "정유", "정해",
    "무자", "무인", "무진", "무오", "무신", "무술",
    "기축", "기묘", "기사", "기미", "기유", "기해",
    "경자", "경인", "경진", "경오", "경신", "경술",
    "신축", "신묘", "신사", "신미", "신유", "신해",
    "임자", "임인", "임진", "임오", "임신", "임술",
    "계축", "계묘", "계사", "계미", "계유", "계해",
]

def _gen_ilju_feature() -> dict:
    ilju   = _pick(_ILJU_LIST, "일주_특징")
    prompt = f"""당신은 팔로워 50만 인스타그래머입니다. 사주를 모르는 일반인도 재미있어야 합니다.
주제: {ilju}일주. "{ilju}일주" 대신 성격 한마디로. 전문 용어 절대 금지.
슬라이드2: 연애 실제 행동. 슬라이드3: 의외의 반전 모습. 슬라이드4: "나도 이런 유형일까?" 2~3문장마다 \\n 줄바꿈.
{_JSON_FORMAT}"""
    result = _call_gemini(prompt)
    result["content_type"] = "일주_특징"
    return result


_FORTUNE_THEMES = [
    "이번 주|전체 운세", "이번 주|금전운", "이번 주|연애운",
    "이번 주|직장운", "오늘|전체 운세", "오늘|관계운",
]

def _gen_daily_fortune() -> dict:
    theme    = _pick(_FORTUNE_THEMES, "오늘의운세")
    period, category = theme.split("|")
    date_str = datetime.now().strftime("%m월 %d일")
    prompt   = f"""당신은 사주 전문가이자 팔로워 50만 인스타그래머입니다. 오늘 날짜: {date_str}
{period} {category} 콘텐츠를 만들어줘.
[훅] 제목: "지금 이 글 보이면 당신한테 하는 말" 식. 12띠 또는 실생활 성향으로 설명.
슬라이드1: 전반적 기운 + 강렬한 훅. 슬라이드2: 운 트이는 띠/성향. 슬라이드3: 조심할 것.
슬라이드4: 행운 팁 + 자연스러운 앱 연결. engagement_q: "내 {category}이 궁금하다면?"
{_JSON_FORMAT}"""
    result = _call_gemini(prompt)
    result["content_type"] = "오늘의운세"
    return result


def _generate_from_topic(topic: str) -> dict:
    prompt = f"""당신은 팔로워 50만 인스타그램 계정 운영자입니다.
주제: {topic}
이 주제로 사주/심리 관점에서 흥미롭게 써줘. 4개 슬라이드, 마지막에 사주 앱 자연스럽게 연결.
{_JSON_FORMAT}"""
    result = _call_gemini(prompt)
    result["content_type"] = "지정주제"
    return result


_GENERATORS = {
    "사주_상식":  _gen_saju_knowledge,
    "궁합":       _gen_compatibility,
    "관계_갈등":  _gen_conflict_story,
    "심리_퀴즈":  _gen_psychology_quiz,
    "일주_특징":  _gen_ilju_feature,
    "오늘의운세": _gen_daily_fortune,
}


def generate_card_content(topic: str = None, content_type: str = None) -> dict:
    if topic:
        print(f"[content_gen] 지정 주제: {topic}")
        return _generate_from_topic(topic)
    if not content_type:
        dow          = datetime.now().weekday()
        content_type = CONTENT_SCHEDULE.get(dow, "관계_갈등")
        print(f"[content_gen] 오늘({DOW_KR[dow]}) 콘텐츠 타입: {content_type}")
    generator = _GENERATORS.get(content_type, _gen_conflict_story)
    try:
        result = generator()
        print(f"[content_gen] 완료: {result.get('display_title', '')}")
        return result
    except Exception as e:
        print(f"[content_gen] {content_type} 실패 ({e}), 대체 생성")
        try:
            return _gen_conflict_story()
        except Exception as e2:
            return _generate_from_topic(random.choice(TOPIC_POOL))
