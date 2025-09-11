import base64
import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import requests


class TelegramAlertBot:
    def __init__(self, bot_token: str):
        """
        Initialize the Telegram Alert Bot

        Args:
            bot_token: Your bot token from @BotFather
        """
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = None

    def send_message(self, text: str) -> Dict[str, Any]:
        """
        Send a simple text message.

        Args:
            text: Text message to send

        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "markdown"}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

    def send_alert(
        self,
        alert_title: str,
        alert_message: str,
        image_source: Optional[str] = None,
        severity: str = "Información",
    ) -> Dict[str, Any]:
        """
        Send an alert with an image and formatted text as caption.

        Args:
            image_source: Image in base64 (string)
            alert_title: Alert title
            alert_message: Alert description
            severity: Severity level (Información, Emergencia)

        Returns:
            Dictionary with the request result
        """
        if not self.chat_id:
            print("Chat ID not set, cannot send alert")
            return {"success": False, "error": "Chat ID not set"}
        severity_emojis = {"Información": "ℹ️", "Emergencia": "⚠️"}

        emoji = severity_emojis.get(severity.upper(), "📢")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y ")

        caption = (
            f"{emoji} *Alerta de {severity.upper()}*\n\n"
            f"*{alert_title}*\n\n"
            f"{alert_message}\n\n"
            f"⏰ {timestamp}"
        )

        url = f"{self.base_url}/sendPhoto"
        data = {"chat_id": self.chat_id, "parse_mode": "markdown", "caption": caption}

        try:
            image_bytes = base64.b64decode(image_source)
            files = {"photo": ("alert.jpg", BytesIO(image_bytes), "image/jpeg")}
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
            return {"success": True, "response": response.json()}
        except Exception as e:
            print(e)
            return {"success": False, "error": f"Failed to send alert: {str(e)}"}

    def get_updates(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent updates (useful for finding chat IDs)

        Returns:
            API response with recent messages
        """
        url = f"{self.base_url}/getUpdates"
        chats = []

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for update in data["result"]:
                chat_id = update["message"]["chat"]["id"]
                name = update["message"]["chat"]["first_name"]

                chat_info = {"chat_id": chat_id, "name": name}

                if not chat_info in chats:
                    chats.append(chat_info)
            return chats

        except requests.exceptions.RequestException as e:
            print(f"Error getting updates: {e}")
            return None

    def set_chat_id(self, chat_id: str):
        self.chat_id = chat_id
