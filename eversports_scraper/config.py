import logging
import os
from typing import Dict, List

logger = logging.getLogger(__name__)

# --- File Paths ---
DATA_DIR = "public/data"
HISTORY_FILE = os.path.join(DATA_DIR, "availability.json")
REPORT_FILE = os.path.join(DATA_DIR, "report.json")

# --- URLs & API ---
TARGET_DATES_CSV_URL = os.environ.get("TARGET_DATES_CSV_URL")

# --- Scraper configuration ---
# Kept deliberately simple: just constants and direct env lookups.
FACILITY_ID = int(os.environ.get("FACILITY_ID", "76443"))
COURT_IDS: List[int] = [77394, 77395, 77396]
COURT_MAPPING: Dict[int, str] = {77394: "Court 1", 77395: "Court 2", 77396: "Court 3"}

SPORT = os.environ.get("SPORT", "badminton")
WIDGET_URL = "https://www.eversports.de/widget/w/c7o9ft"
API_BASE = "https://www.eversports.de/widget/api/slot"

# Headers to mimic a browser
COMMON_HEADERS: Dict[str, str] = {
    "User-Agent": os.environ.get(
        "SCRAPER_USER_AGENT",
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": os.environ.get("SCRAPER_ACCEPT_LANGUAGE", "de-DE,de;q=0.9,en;q=0.8"),
    "Referer": os.environ.get("SCRAPER_REFERER", WIDGET_URL),
    "Origin": os.environ.get("SCRAPER_ORIGIN", "https://www.eversports.de"),
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
}

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.warning("Telegram configuration incomplete. Skipping notifications.")
