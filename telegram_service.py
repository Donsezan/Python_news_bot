import requests

class TelegramService:
    def __init__(self, BOT_TOKEN, CHAT_ID):
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID

    CAPTION_LIMIT = 1024

    def post_to_telegram(self, message_text, images, href):
        url_suffix = f"\n\n{href}"
        if images:
            max_summary = self.CAPTION_LIMIT - len(url_suffix)
            if len(message_text) > max_summary:
                message_text = message_text[:max_summary - 1] + "…"
        message_text = message_text + url_suffix
        if images:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMediaGroup"
            mediaGroup = [
                {'type': 'photo',
                'media': images[0],
                'caption': message_text,
                'parse_mode': 'HTML'}
            ]
            if len(images) > 1:
                for image in images[1:9]:
                    mediaGroup.append({'type': 'photo', 'media': image})
            payload = {
                "chat_id": self.chat_id,
                "media": mediaGroup
            }
            
            try:
                resp = requests.post(url, json=payload)
                print(f"Telegram response: {resp.json()}")
                return True
            except Exception as e:
                print(f"Error posting to Telegram: {e}")
                return False
        else:
            # If no images, send as a text message
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            params = {"chat_id": self.chat_id, "text": message_text}

            try:
                resp = requests.get(url, params=params)
                print(f"Telegram response: {resp.json()}")
                return True
            except Exception as e:
                print(f"Error posting to Telegram: {e}")
                return False
