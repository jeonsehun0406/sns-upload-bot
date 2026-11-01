"""텔레그램 봇 - 미리보기 전송 + 승인/취소 처리"""

import json
import logging
import uuid
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.token   = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api     = f"https://api.telegram.org/bot{self.token}"
        self._pending: dict = {}  # post_id → {content, images}

    # ── webhook 등록 ──────────────────────────────────────
    def set_webhook(self, url: str):
        r = requests.post(f"{self.api}/setWebhook", json={"url": url}, timeout=10)
        logger.info(f"setWebhook: {r.json()}")

    def delete_webhook(self):
        requests.post(f"{self.api}/deleteWebhook", timeout=10)

    # ── 미리보기 전송 ─────────────────────────────────────
    def send_preview(self, content: dict, image_paths: list):
        post_id = str(uuid.uuid4())[:8]
        self._pending[post_id] = {"content": content, "images": image_paths}

        title    = content.get("display_title", "")
        category = content.get("category", "")
        caption  = content.get("caption", "")[:200]
        hashtags = content.get("hashtags", "")
        ct       = content.get("content_type", "")

        text = (
            f"📋 *오늘의 콘텐츠 미리보기*\n\n"
            f"📌 제목: {title}\n"
            f"🏷 유형: {ct} / {category}\n"
            f"🖼 이미지: {len(image_paths)}장\n\n"
            f"📝 캡션:\n{caption}...\n\n"
            f"🏷 {hashtags[:80]}\n\n"
            f"Instagram + Threads 업로드할까요?"
        )

        keyboard = {"inline_keyboard": [[
            {"text": "✅ 업로드", "callback_data": f"approve_{post_id}"},
            {"text": "❌ 취소",   "callback_data": f"cancel_{post_id}"},
        ]]}

        try:
            with open(image_paths[0], "rb") as f:
                r = requests.post(
                    f"{self.api}/sendPhoto",
                    data={
                        "chat_id":      self.chat_id,
                        "caption":      text,
                        "parse_mode":   "Markdown",
                        "reply_markup": json.dumps(keyboard),
                    },
                    files={"photo": f},
                    timeout=30,
                )
            logger.info(f"미리보기 전송: {r.status_code} post_id={post_id}")
        except Exception as e:
            logger.error(f"미리보기 전송 실패: {e}")

    # ── 업데이트 처리 ─────────────────────────────────────
    def handle_update(self, update: dict):
        if "callback_query" not in update:
            return

        query      = update["callback_query"]
        data       = query.get("data", "")
        message_id = query["message"]["message_id"]

        if data.startswith("approve_"):
            post_id = data.removeprefix("approve_")
            pending = self._pending.pop(post_id, None)

            if not pending:
                self._answer_callback(query["id"], "만료된 요청입니다")
                return

            self._answer_callback(query["id"], "업로드 시작!")
            self._edit_caption(message_id, "⏳ 업로드 중...")

            try:
                from uploader import upload_all
                results = upload_all(
                    pending["images"],
                    pending["content"].get("caption", ""),
                    pending["content"].get("hashtags", ""),
                    platforms=["instagram", "threads"],
                )
                lines = "✅ 업로드 완료!\n"
                for p, v in results.items():
                    lines += f"  • {p}: {v}\n"
                self._edit_caption(message_id, lines)

            except Exception as e:
                logger.error(f"업로드 실패: {e}", exc_info=True)
                self._edit_caption(message_id, f"❌ 업로드 실패:\n{str(e)[:300]}")

        elif data.startswith("cancel_"):
            post_id = data.removeprefix("cancel_")
            self._pending.pop(post_id, None)
            self._answer_callback(query["id"], "취소됨")
            self._edit_caption(message_id, "🚫 업로드 취소됨")

    # ── 유틸 ─────────────────────────────────────────────
    def _edit_caption(self, message_id: int, text: str):
        requests.post(f"{self.api}/editMessageCaption", json={
            "chat_id":    self.chat_id,
            "message_id": message_id,
            "caption":    text,
        }, timeout=10)

    def _answer_callback(self, callback_id: str, text: str = ""):
        requests.post(f"{self.api}/answerCallbackQuery", json={
            "callback_query_id": callback_id,
            "text": text,
        }, timeout=10)

    def send_message(self, text: str):
        requests.post(f"{self.api}/sendMessage", json={
            "chat_id":  self.chat_id,
            "text":     text,
            "parse_mode": "Markdown",
        }, timeout=10)
