import logging
import os

logger = logging.getLogger(__name__)

# --- File Paths ---
DATA_DIR = "public/data"
HISTORY_FILE = os.path.join(DATA_DIR, "availability.json")
REPORT_FILE = os.path.join(DATA_DIR, "report.json")

# --- URLs & API ---
TARGET_DATES_CSV_URL = os.environ.get("TARGET_DATES_CSV_URL")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.warning("Telegram configuration incomplete. Skipping notification.")
