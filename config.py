import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
FONTS_DIR  = BASE_DIR / "fonts"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
FAL_KEY        = os.getenv("FAL_KEY", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
PORT = int(os.getenv("PORT", 8000))

APP_NAME = "운명의문"
APP_HASHTAGS = [
    "#운명의문", "#사주", "#사주팔자", "#심리테스트", "#운세",
    "#심리", "#MBTI", "#자기계발", "#심리상담", "#오늘의운세"
]

TOPIC_POOL = [
    "회피형 애착 유형의 특징과 극복법",
    "번아웃을 알리는 몸의 신호 5가지",
    "자존감 낮은 사람이 하는 말버릇",
    "감정노동이 심한 사람들의 공통점",
    "완벽주의자가 사실 두려워하는 것",
    "MBTI별 스트레스 받을 때 행동패턴",
    "진짜 친구와 가짜 친구를 구분하는 법",
    "무의식이 보내는 신호 해석하기",
    "사주로 보는 나의 숨겨진 재능",
    "올해 운세를 바꾸는 심리 습관",
    "연애에서 상처받는 이유 심리학으로 보기",
    "돈을 끌어당기는 사람들의 심리",
    "불안을 잠재우는 3가지 심리 기술",
    "나를 힘들게 하는 사람 대처법",
    "좋은 기운을 부르는 사주 활용법",
]
