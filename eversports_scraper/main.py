import argparse
import csv
import io
import logging
import sys
from datetime import datetime, timedelta
from typing import List

import requests

from eversports_scraper import config, persist, scraper, telegram_notifier

# --- Logging Setup ---

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool):
    """Configures logging to stderr."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s]: %(name)s:%(lineno)d | %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


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
            if not row:
                continue
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


def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Scrape Eversports for free badminton courts.")
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--days", type=int, default=3, help="Number of days to check. Defaults to 3.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def print_availability_report(day_data):
    """Prints the formatted availability report to stdout."""
    date_str = day_data.date
    slots = day_data.slots

    print(f"\n--- Availability Report for {date_str} ---")

    for slot in slots:
        prefix = "[NEW]      " if slot.is_new else "[AVAILABLE]"
        print(f"{prefix} {slot.time}: {', '.join(slot.courts)}")

    if slots:
        print(f"Summary: Found {len(slots)} available time slots for {date_str}!")
    else:
        print(f"Summary: No courts available for {date_str}.")


def get_target_dates_list(args) -> List[str]:
    """Determines the list of target dates to scrape."""
    logger.info("Fetching target dates from CSV...")
    target_dates = fetch_target_dates(config.TARGET_DATES_CSV_URL)

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

    return target_dates


def notify_if_needed(total_new_slots: int, new_slots_messages: List[str], num_days: int):
    """Sends a Telegram notification if new slots were found."""
    if total_new_slots > 0:
        print(f"\n*** Total NEW slots found across {num_days} days: {total_new_slots} ***")

        # Send Telegram notification
        message = f"🏸 *New Badminton Slots Found!* ({total_new_slots})\n\n" + "\n\n".join(new_slots_messages)
        message += "\n\n[Book Now](https://www.eversports.de/widget/w/c7o9ft)"
        telegram_notifier.send_telegram_message(message)

    else:
        print(f"\nNo new slots found across {num_days} days.")


def main():
    args = parse_arguments()
    setup_logging(args.verbose)

    target_dates = get_target_dates_list(args)
    print(f"Checking availability for {len(target_dates)} days: {', '.join(target_dates)}")

    all_slots = scraper.get_all_slots()
    history = persist.load_history()

    current_state = {}
    results = []
    total_new_slots = 0
    new_slots_messages = []

    for date_str in target_dates:
        day_data = scraper.get_day_availability(date_str, all_slots, history)

        if day_data:
            print_availability_report(day_data)
            total_new_slots += day_data.new_count
            current_state[date_str] = day_data.free_slots_map
            results.append(day_data)

            # Collect new slots for notification
            new_slots = [s for s in day_data.slots if s.is_new]
            if new_slots:
                msg_lines = [f"*{date_str}*:"]
                for s in new_slots:
                    msg_lines.append(f"  - {s.time} ({', '.join(s.courts)})")
                new_slots_messages.append("\n".join(msg_lines))

        elif date_str in history:
            # Preserve history if fetch failed
            current_state[date_str] = history[date_str]

    persist.save_history(current_state)
    persist.save_report(results)

    notify_if_needed(total_new_slots, new_slots_messages, len(target_dates))


if __name__ == "__main__":
    main()
