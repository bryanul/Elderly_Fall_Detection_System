import base64
import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import requests


class TelegramAlertBot:
    def __init__(self, bot_token: str, chat_id: Optional[str] = None):
        """
        Initialize the Telegram Alert Bot

        Args:
            bot_token: Your bot token from @BotFather
        """
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id
        self.available_chats = []

    def send_alert(
        self,
        alert_title: str,
        alert_message: str,
        image_source: Optional[str] = None,
        severity: str = "Información",
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an alert with an image and formatted text as caption.

        Args:
            image_source: Image in base64 (string)
            alert_title: Alert title
            alert_message: Alert description
            chat_id: Optional chat ID to send the alert to (overrides self.chat_id)
            severity: Severity level (Información, Emergencia)

        Returns:
            Dictionary with the request result
        """
        if not self.chat_id and not chat_id:
            print("Chat ID not set, cannot send alert")
            return {"success": False, "error": "Chat ID not set"}
        severity_emojis = {"Información": "ℹ️", "Emergencia": "⚠️"}

        emoji = severity_emojis.get(severity.upper(), "📢")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y ")

        caption = (
            f"{emoji} *{severity.upper()}*\n\n"
            f"*{alert_title}*\n\n"
            f"{alert_message}\n\n"
            f"⏰ {timestamp}"
        )

        url = f"{self.base_url}/sendPhoto"

        chat_id_to_send = chat_id if chat_id else self.chat_id
        data = {
            "chat_id": chat_id_to_send,
            "parse_mode": "markdown",
            "caption": caption,
        }

        try:
            image_bytes = base64.b64decode(image_source)
            files = {"photo": ("alert.jpg", BytesIO(image_bytes), "image/jpeg")}
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
            return {"success": True, "response": response.json()}
        except Exception as e:
            print(e)
            return {"success": False, "error": f"Failed to send alert: {str(e)}"}

    def handle_webhook(self, update: dict) -> None:
        """
        Handle incoming updates from Telegram (called by the webhook).
        Args:
            update: The update payload received from Telegram
        """
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        name = message.get("chat", {}).get("first_name")
        text = message.get("text", "")

        chat_info = {"chat_id": chat_id, "name": name}

        if text == "/start":
            self.send_alert(
                "Bienvenido a FallGuardUL",
                "Para continuar con la configuración, haz click en el botón de *Actualizar chats*",
                self._encode_info_image(),
                "Información",
                chat_id,
            )

        if not chat_info in self.available_chats:
            self.available_chats.append(chat_info)

    def set_chat_id(self, chat_id: str):
        self.chat_id = chat_id

    def _encode_info_image(self):
        image_path = "app/alerts/info.png"
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            return image_base64
