import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from urllib.parse import urlencode

import cloudscraper

from eversports_scraper import config
from eversports_scraper.models import DayAvailability, Slot

logger = logging.getLogger(__name__)


def get_all_slots() -> List[str]:
    """Generates a list of all possible slot start times based on the facility's schedule."""
    start_hour = 10
    start_minute = 15
    end_hour = 22
    end_minute = 15
    slot_duration_minutes = 45

    slots = []
    current_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    end_time = datetime.now().replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

    while current_time <= end_time:
        slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=slot_duration_minutes)

    logger.debug(f"Generated {len(slots)} slots: {slots}")
    return slots


def build_url(day_iso: str) -> str:
    """Constructs the API URL for a specific date."""
    qs = {"facilityId": config.FACILITY_ID, "sport": config.SPORT, "startDate": day_iso}
    repeated = "&".join(f"courts%5B%5D={cid}" for cid in config.COURT_IDS)
    url = f"{config.API_BASE}?{urlencode(qs)}&{repeated}"
    logger.debug(f"Built URL: {url}")
    return url


def fetch_booked_slots(date_str: str) -> Optional[Dict]:
    """Fetches booked slots from the Eversports API using cloudscraper."""
    full_url = build_url(date_str)
    logger.info(f"Fetching data for {date_str} from {full_url}")

    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(full_url, headers=config.COMMON_HEADERS, timeout=10)
        logger.debug(f"Response status: {response.status_code}")
        response.raise_for_status()
        data: Dict = response.json()
        return data
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        if "response" in locals() and response.status_code == 403:
            logger.error("Cloudflare blocked the request even with cloudscraper.")
        return None


def parse_booked_slots(data: Dict, date_str: str, all_slots: List[str]) -> Dict[str, Set[int]]:
    """Parses the API response to map booked slots to court IDs."""
    if "slots" not in data:
        logger.error("Unexpected JSON format. 'slots' key missing.")
        logger.debug(f"Response data: {data}")
        return {}

    booked_courts_by_slot: Dict[str, Set[int]] = {slot: set() for slot in all_slots}

    for booking in data["slots"]:
        if booking.get("date") == date_str:
            start_raw = booking.get("start")  # e.g., "1100"
            court_id = booking.get("court")

            if start_raw and court_id:
                start_formatted = f"{start_raw[:2]}:{start_raw[2:]}"
                if start_formatted in booked_courts_by_slot:
                    booked_courts_by_slot[start_formatted].add(court_id)
                else:
                    logger.warning(f"Booking found for slot {start_formatted} which is not in our generated schedule.")

    return booked_courts_by_slot


def calculate_free_slots(booked_courts_by_slot: Dict[str, Set[int]], all_slots: List[str]) -> Dict[str, List[int]]:
    """Calculates which courts are free for each slot."""
    all_court_ids = set(config.COURT_IDS)
    free_slots_map = {}

    for slot in all_slots:
        booked_ids = booked_courts_by_slot.get(slot, set())
        free_ids = list(all_court_ids - booked_ids)
        if free_ids:
            free_slots_map[slot] = free_ids

    return free_slots_map


def get_day_availability(date_str: str, all_slots: List[str], history: Dict) -> Optional[DayAvailability]:
    """Fetches data and returns a structured availability object for a single date."""
    data = fetch_booked_slots(date_str)

    if not data:
        print(f"Failed to fetch data for {date_str}.")
        return None

    booked_courts_by_slot = parse_booked_slots(data, date_str, all_slots)
    free_slots_map = calculate_free_slots(booked_courts_by_slot, all_slots)

    # Compare with history to identify new slots
    prev_free_slots_map = history.get(date_str, {})

    slots_data = []
    new_slots_count = 0

    for slot in sorted(free_slots_map.keys()):
        free_court_ids = free_slots_map[slot]
        free_court_names = [config.COURT_MAPPING.get(cid, f"Unknown({cid})") for cid in sorted(free_court_ids)]

        # Check for new availability
        prev_free_courts = set(prev_free_slots_map.get(slot, []))
        current_free_courts = set(free_court_ids)
        newly_free_courts = current_free_courts - prev_free_courts

        is_new = bool(newly_free_courts)
        if is_new:
            new_slots_count += 1

        slots_data.append(Slot(time=slot, courts=free_court_names, court_ids=free_court_ids, is_new=is_new))

    return DayAvailability(
        date=date_str,
        slots=slots_data,
        new_count=new_slots_count,
        free_slots_map=free_slots_map,
    )
