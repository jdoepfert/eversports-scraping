import csv
import io
import logging
import sys
from datetime import datetime, timedelta
from typing import List

import requests

from eversports_scraper import config, persist, scraper, telegram_notifier
from eversports_scraper.models import TargetDate

logger = logging.getLogger(__name__)


def fetch_target_dates(url: str) -> List[TargetDate]:
    """Fetches target dates with optional time intervals from a Google Sheet CSV.
    
    Expected CSV format:
    Column A: Date in DD.MM.YYYY format
    Column B: Start time in HH:MM format (optional)
    Column C: End time in HH:MM format (optional)
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse CSV
        f = io.StringIO(response.text)
        reader = csv.reader(f)
        target_dates = []

        for row in reader:
            if not row:
                continue
            date_str = row[0].strip()
            
            # Skip likely header rows (case-insensitive check for common header text)
            if date_str.lower() in ['date', 'datum', 'day', 'tag']:
                logger.debug(f"Skipping header row: {row}")
                continue
            
            try:
                # Parse DD.MM.YYYY and convert to YYYY-MM-DD
                dt = datetime.strptime(date_str, "%d.%m.%Y")
                iso_date = dt.strftime("%Y-%m-%d")
                
                # Parse optional time columns
                start_time = None
                end_time = None
                
                if len(row) > 1 and row[1].strip():
                    start_time = row[1].strip()
                    # Validate time format
                    try:
                        datetime.strptime(start_time, "%H:%M")
                    except ValueError:
                        logger.warning(f"Invalid start time format '{start_time}' for {date_str}, ignoring")
                        start_time = None
                
                if len(row) > 2 and row[2].strip():
                    end_time = row[2].strip()
                    # Validate time format
                    try:
                        datetime.strptime(end_time, "%H:%M")
                    except ValueError:
                        logger.warning(f"Invalid end time format '{end_time}' for {date_str}, ignoring")
                        end_time = None
                
                target_dates.append(TargetDate(
                    date=iso_date,
                    start_time=start_time,
                    end_time=end_time
                ))
            except ValueError:
                # Silently skip rows that don't parse as dates (likely headers or invalid entries)
                logger.debug(f"Skipping row with invalid date format: {date_str}")

        return target_dates
    except Exception as e:
        logger.error(f"Failed to fetch target dates: {e}")
        return []


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


def check_time_overlap(slot_time: str, target_date: TargetDate) -> bool:
    """Checks if a slot overlaps with the target date's time interval.
    
    Args:
        slot_time: Start time of the slot in HH:MM format (e.g., "10:15")
        target_date: TargetDate with optional start_time and end_time
    
    Returns:
        True if the slot overlaps with the interval or no interval is specified
    """
    # If no time interval specified, include all slots
    if target_date.start_time is None or target_date.end_time is None:
        return True
    
    # Parse times to compare
    # Slot is 45 minutes long
    slot_start = datetime.strptime(slot_time, "%H:%M").time()
    slot_end = (datetime.strptime(slot_time, "%H:%M") + timedelta(minutes=45)).time()
    
    interval_start = datetime.strptime(target_date.start_time, "%H:%M").time()
    interval_end = datetime.strptime(target_date.end_time, "%H:%M").time()
    
    # Check if there's any overlap
    # Slots overlap if: slot_start < interval_end AND slot_end > interval_start
    return slot_start < interval_end and slot_end > interval_start


def get_target_dates_list(start_date_arg: str | None, days_arg: int) -> List[TargetDate]:
    """Determines the list of target dates to scrape."""
    logger.info("Fetching target dates from CSV...")
    target_dates = []
    if config.TARGET_DATES_CSV_URL:
        target_dates = fetch_target_dates(config.TARGET_DATES_CSV_URL)

    if not target_dates:
        logger.warning("No target dates found in google sheet")
        if start_date_arg:
            try:
                start_date = datetime.strptime(start_date_arg, "%Y-%m-%d")
            except ValueError:
                logger.error("Error: Start date must be in YYYY-MM-DD format.")
                sys.exit(1)
        else:
            start_date = datetime.now()

        for i in range(days_arg):
            current_date = start_date + timedelta(days=i)
            target_dates.append(TargetDate(
                date=current_date.strftime("%Y-%m-%d"),
                start_time=None,
                end_time=None
            ))

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


def run(start_date: str | None = None, days: int = 3):
    """Core orchestration logic. Loops through target dates, checks for availability, and 
    sends notifications when new slots are found."""
    
    target_dates = get_target_dates_list(start_date, days)
    date_strs = [td.date for td in target_dates]
    print(f"Checking availability for {len(target_dates)} days: {', '.join(date_strs)}")

    all_slots = scraper.get_all_slots()
    history = persist.load_history()

    current_state = {}
    results = []
    total_new_slots = 0
    new_slots_messages = []

    for target_date in target_dates:
        date_str = target_date.date
        day_data = scraper.get_day_availability(date_str, all_slots, history)

        if day_data:
            print_availability_report(day_data)
            total_new_slots += day_data.new_count
            current_state[date_str] = day_data.free_slots_map
            results.append(day_data)

            # Collect new slots for notification, filtered by time interval
            new_slots = [s for s in day_data.slots if s.is_new]
            
            # Filter slots based on time interval
            filtered_new_slots = [
                s for s in new_slots 
                if check_time_overlap(s.time, target_date)
            ]
            
            if filtered_new_slots:
                msg_lines = [f"*{date_str}*:"]
                for s in filtered_new_slots:
                    msg_lines.append(f"  - {s.time} ({', '.join(s.courts)})")
                new_slots_messages.append("\n".join(msg_lines))

        elif date_str in history:
            # Preserve history if fetch failed
            current_state[date_str] = history[date_str]

    persist.save_history(current_state)
    persist.save_report(results)

    # Recalculate total based on filtered slots
    total_filtered_new_slots = sum(
        len(msg.split('\n')) - 1  # Subtract 1 for the date header line
        for msg in new_slots_messages
    )
    
    notify_if_needed(total_filtered_new_slots, new_slots_messages, len(target_dates))
