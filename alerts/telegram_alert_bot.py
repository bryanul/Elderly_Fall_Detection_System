import base64
from io import BytesIO

import requests
import datetime
from typing import Dict, Any


class TelegramAlertBot:
    def __init__(self, bot_token: str):
        """
        Initialize the Telegram Alert Bot

        Args:
            bot_token: Your bot token from @BotFather
        """
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        """
        Send a simple text message.

        Args:
            chat_id: Target chat ID or username
            text: Text message to send

        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "markdown"}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

    def send_alert(
        self,
        chat_id: str,
        image_source: str,
        alert_title: str,
        alert_message: str,
        severity: str = "INFO",
    ) -> Dict[str, Any]:
        """
        Send an alert with an image and formatted text as caption.

        Args:
            chat_id: Target chat ID or username
            image_source: Image in base64 (string)
            alert_title: Alert title
            alert_message: Alert description
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)

        Returns:
            Dictionary with the request result
        """
        severity_emojis = {"INFO": "ℹ️", "WARNING": "⚠️"}

        emoji = severity_emojis.get(severity.upper(), "📢")
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        caption = (
            f"{emoji} *{severity.upper()} ALERT*\n\n"
            f"*{alert_title}*\n\n"
            f"{alert_message}\n\n"
            f"⏰ {timestamp}"
        )

        url = f"{self.base_url}/sendPhoto"
        data = {"chat_id": chat_id, "parse_mode": "markdown", "caption": caption}

        try:
            image_bytes = base64.b64decode(image_source)
            files = {"photo": ("alert.jpg", BytesIO(image_bytes), "image/jpeg")}
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
            return {"success": True, "response": response.json()}
        except Exception as e:
            return {"success": False, "error": f"Failed to send alert: {str(e)}"}

    def get_updates(self) -> Dict[str, Any]:
        """
        Get recent updates (useful for finding chat IDs)

        Returns:
            API response with recent messages
        """
        url = f"{self.base_url}/getUpdates"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting updates: {e}")
            return {"ok": False, "error": str(e)}
