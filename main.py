import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
import json
import os
from typing import List, Dict

import scraper
import telegram_notifier

# --- Configuration ---
import requests
import csv
import io

# ... existing imports ...

# --- Configuration ---
DATA_DIR = "docs/data"
HISTORY_FILE = os.path.join(DATA_DIR, "availability.json")
REPORT_FILE = os.path.join(DATA_DIR, "report.json")
TARGET_DATES_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT2NjrFvgP0Qr5IdPqZsBg0XXVnv3M8mK6Hy9QTSyo_r3IMPO-7fYyfbq-e0TyYFtcRI-JaAH1SmitB/pub?gid=0&single=true&output=csv"

# --- Logging Setup ---

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool):
    """Configures logging to stderr."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)-8s | %(lineno)4d | %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )

# --- Helper Functions ---

def fetch_target_dates(url: str) -> List[str]:
    """Fetches target dates from a Google Sheet CSV."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse CSV
        f = io.StringIO(response.text)
        reader = csv.reader(f)
        dates = []
        
        for row in reader:
            if not row: continue
            date_str = row[0].strip()
            try:
                # Parse DD.MM.YYYY and convert to YYYY-MM-DD
                dt = datetime.strptime(date_str, "%d.%m.%Y")
                dates.append(dt.strftime("%Y-%m-%d"))
            except ValueError:
                logger.warning(f"Skipping invalid date format: {date_str}")
                
        return dates
    except Exception as e:
        logger.error(f"Failed to fetch target dates: {e}")
        return []

# --- Persistence ---

def ensure_data_dir():
    """Ensures the data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_history() -> Dict:
    """Loads the previous availability state from a JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        logger.warning("Failed to load history file. Starting fresh.")
        return {}

def save_history(history: Dict):
    """Saves the current availability state to a JSON file."""
    ensure_data_dir()
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to save history: {e}")

def save_report(results: List[Dict]):
    """Saves the availability report to a JSON file."""
    ensure_data_dir()
    try:
        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "days": results
        }
        with open(REPORT_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved report to {REPORT_FILE}")
    except IOError as e:
        logger.error(f"Failed to save report: {e}")

# --- Main Execution ---

def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Scrape Eversports for free badminton courts.")
    parser.add_argument(
        "--start-date", 
        type=str, 
        help="Start date in YYYY-MM-DD format. Defaults to today."
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=3,
        help="Number of days to check. Defaults to 1."
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging."
    )
    return parser.parse_args()

def print_availability_report(day_data: Dict):
    """Prints the formatted availability report to stdout."""
    date_str = day_data["date"]
    slots = day_data["slots"]
    
    print(f"\n--- Availability Report for {date_str} ---")
    
    for slot in slots:
        prefix = "[NEW]      " if slot["is_new"] else "[AVAILABLE]"
        print(f"{prefix} {slot['time']}: {', '.join(slot['courts'])}")

    if slots:
        print(f"Summary: Found {len(slots)} available time slots for {date_str}!")
    else:
        print(f"Summary: No courts available for {date_str}.")

def main():
    args = parse_arguments()
    setup_logging(args.verbose)
    
    target_dates = []

    logger.info("Fetching target dates from CSV...")
    target_dates = fetch_target_dates(TARGET_DATES_CSV_URL)
    
    if not target_dates:
        logger.warning("No target dates found in google sheet")
        if args.start_date:
            try:
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            except ValueError:
                logger.error("Error: Start date must be in YYYY-MM-DD format.")
                sys.exit(1)
        else:
            start_date = datetime.now()
            
        for i in range(args.days):
            current_date = start_date + timedelta(days=i)
            target_dates.append(current_date.strftime("%Y-%m-%d"))
    
    if not target_dates:
        logger.error("No target dates found. Exiting.")
        sys.exit(1)
        
    print(f"Checking availability for {len(target_dates)} days: {', '.join(target_dates)}")

    all_slots = scraper.get_all_slots()
    history = load_history()
    current_state = {}
    total_new_slots = 0
    results = []
    new_slots_messages = []

    for date_str in target_dates:
        day_data = scraper.get_day_availability(date_str, all_slots, history)
        
        if day_data:
            print_availability_report(day_data)
            total_new_slots += day_data["new_count"]
            current_state[date_str] = day_data["free_slots_map"]
            results.append(day_data)
            
            # Collect new slots for notification
            new_slots = [s for s in day_data["slots"] if s["is_new"]]
            if new_slots:
                msg_lines = [f"*{date_str}*:"]
                for s in new_slots:
                    msg_lines.append(f"  - {s['time']} ({', '.join(s['courts'])})")
                new_slots_messages.append("\n".join(msg_lines))

        elif date_str in history:
             # Preserve history if fetch failed
             current_state[date_str] = history[date_str]

    save_history(current_state)
    save_report(results)
    
    if total_new_slots > 0:
        print(f"\n*** Total NEW slots found across {len(target_dates)} days: {total_new_slots} ***")
        
        # Send Telegram notification
        message = f"🏸 *New Badminton Slots Found!* ({total_new_slots})\n\n" + "\n\n".join(new_slots_messages)
        message += "\n\n[Book Now](https://www.eversports.de/widget/w/c7o9ft)"
        telegram_notifier.send_telegram_message(message)
        
    else:
        print(f"\nNo new slots found across {len(target_dates)} days.")

if __name__ == "__main__":
    main()
