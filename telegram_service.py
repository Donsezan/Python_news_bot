import logging
import requests

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, BOT_TOKEN, CHAT_ID):
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID

    CAPTION_LIMIT = 1024

    def _post(self, url, payload):
        try:
            resp = requests.post(url, json=payload, timeout=20)
        except requests.RequestException as e:
            logger.error(f"[tg] Network error: {e}")
            return False

        try:
            body = resp.json()
        except ValueError:
            logger.error(f"[tg] Non-JSON response ({resp.status_code}): {resp.text[:200]}")
            return False

        if not resp.ok or not body.get("ok"):
            logger.error(f"[tg] API error ({resp.status_code}): {body}")
            return False
        return True

    def post_to_telegram(self, message_text, images, href):
        if not message_text or not message_text.strip():
            logger.warning("[tg] Refusing to post empty message")
            return False

        url_suffix = f"\n\n{href}"
        if images:
            max_summary = self.CAPTION_LIMIT - len(url_suffix)
            if len(message_text) > max_summary:
                message_text = message_text[:max_summary - 1] + "…"
        message_text += url_suffix

        if images:
            media = [{'type': 'photo', 'media': images[0],
                      'caption': message_text, 'parse_mode': 'HTML'}]
            media += [{'type': 'photo', 'media': img} for img in images[1:9]]
            return self._post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMediaGroup",
                {"chat_id": self.chat_id, "media": media},
            )

        text = message_text[:4090] + "…" if len(message_text) > 4096 else message_text
        return self._post(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
        )
