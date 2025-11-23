import requests
import logging

from eversports_scraper import config

logger = logging.getLogger(__name__)

def send_telegram_message(message: str):
    """Sends a message to the configured Telegram chat."""
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.warning("Telegram configuration missing. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Telegram notification sent successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
