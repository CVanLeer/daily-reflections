"""
Send delivery notifications for completed daily reflections.
Supports Telegram (audio + summary message).
"""

import os
import requests


TELEGRAM_API = "https://api.telegram.org/bot{token}"


def send_telegram(audio_path: str, summary: str = None):
    """Send the audio file + optional summary to Chris via Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_USER_ID")

    if not token or not chat_id:
        print("   Telegram: TELEGRAM_BOT_TOKEN or TELEGRAM_USER_ID not set, skipping.")
        return False

    base_url = TELEGRAM_API.format(token=token)

    try:
        # Send summary message first
        if summary:
            requests.post(
                f"{base_url}/sendMessage",
                json={"chat_id": chat_id, "text": summary, "parse_mode": "Markdown"},
                timeout=10,
            )

        # Send audio file
        with open(audio_path, "rb") as f:
            resp = requests.post(
                f"{base_url}/sendAudio",
                data={"chat_id": chat_id, "title": "Daily Reflection", "performer": "JEJ"},
                files={"audio": (os.path.basename(audio_path), f, "audio/mpeg")},
                timeout=120,
            )

        if resp.status_code == 200:
            print("   Telegram: Audio sent successfully.")
            return True
        else:
            print(f"   Telegram: Failed ({resp.status_code}): {resp.text[:200]}")
            return False

    except Exception as e:
        print(f"   Telegram: Error — {e}")
        return False
