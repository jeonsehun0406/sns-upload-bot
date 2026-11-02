"""
SNS 자동 업로드 봇 - Render Web Service
- 매일 오전 9시 (KST): 콘텐츠 생성 → 카드 이미지 생성 → 텔레그램 미리보기
- 텔레그램 ✅ 승인 시: Instagram + Threads 업로드
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from config import RENDER_EXTERNAL_URL, PORT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_bot = None
_log_file = os.path.join(os.path.dirname(__file__), "upload_log.json")


def get_bot():
    global _bot
    if _bot is None:
        from bot import TelegramBot
        _bot = TelegramBot()
    return _bot


def _load_log():
    if os.path.exists(_log_file):
        with open(_log_file, encoding="utf-8") as f:
            return json.load(f)
    return []


def daily_job():
    """매일 09:00 KST: 콘텐츠 생성 → 이미지 → 텔레그램 미리보기 전송"""
    logger.info("=== daily_job 시작 ===")
    bot = get_bot()
    try:
        from content_gen import generate_card_content
        from image_maker import create_card_set

        log      = _load_log()
        post_idx = len(log) + 1

        logger.info("콘텐츠 생성 중...")
        content = generate_card_content()
        logger.info(f"제목: {content.get('display_title')}")

        logger.info("이미지 생성 중...")
        image_paths = create_card_set(content, post_idx)
        logger.info(f"이미지 {len(image_paths)}장 생성 완료")

        bot.send_preview(content, image_paths)
        logger.info("텔레그램 미리보기 전송 완료")

    except Exception as e:
        logger.error(f"daily_job 오류: {e}", exc_info=True)
        try:
            bot.send_message(f"❌ 콘텐츠 생성 오류:\n`{str(e)[:300]}`")
        except Exception:
            pass


# ── Flask 라우트 ──────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    """텔레그램 webhook 수신"""
    update = request.get_json(silent=True)
    if update:
        get_bot().handle_update(update)
    return "OK", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "sns-upload-bot"}), 200


@app.route("/test", methods=["GET"])
def test():
    """테스트: 지금 바로 daily_job 1회 실행 (브라우저에서 URL 열면 실행됨)"""
    import threading
    t = threading.Thread(target=daily_job, daemon=True)
    t.start()
    return jsonify({"status": "triggered", "message": "텔레그램 확인하세요"}), 200


@app.route("/log", methods=["GET"])
def log():
    return jsonify(_load_log()[-10:]), 200


# ── 앱 시작 시 초기화 (gunicorn 포함) ────────────────────

def _startup():
    """gunicorn/직접 실행 모두에서 호출되는 초기화"""
    # Webhook 등록
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/webhook"
        get_bot().set_webhook(webhook_url)
        logger.info(f"Telegram webhook 등록: {webhook_url}")
    else:
        logger.warning("RENDER_EXTERNAL_URL 없음 — webhook 미등록 (로컬 테스트 모드)")

    # APScheduler — 매일 KST 09:00
    kst       = pytz.timezone("Asia/Seoul")
    scheduler = BackgroundScheduler(timezone=kst)
    scheduler.add_job(
        daily_job,
        CronTrigger(hour=9, minute=0, timezone=kst),
        id="daily_sns",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("스케줄러 시작 — 매일 KST 09:00 실행")


# gunicorn은 모듈을 import할 때 이 코드가 실행됨
_startup()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
