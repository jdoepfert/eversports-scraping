import os
import logging

logger = logging.getLogger(__name__)

# --- File Paths ---
DATA_DIR = "docs/data"
HISTORY_FILE = os.path.join(DATA_DIR, "availability.json")
REPORT_FILE = os.path.join(DATA_DIR, "report.json")

# --- URLs & API ---
TARGET_DATES_CSV_URL = os.environ.get(
    "TARGET_DATES_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vT2NjrFvgP0Qr5IdPqZsBg0XXVnv3M8mK6Hy9QTSyo_r3IMPO-7fYyfbq-e0TyYFtcRI-JaAH1SmitB/pub?gid=0&single=true&output=csv",
)

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.warning("Telegram configuration incomplete. Skipping notification.")