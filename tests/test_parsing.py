import json
from datetime import datetime, timedelta

# Mock configuration
COURT_IDS = [77394, 77395, 77396]


def get_all_slots():
    """Generates a list of all possible slot start times based on the facility's schedule."""
    # Schedule starts at 10:15 and ends with the last slot at 22:15
    start_hour = 10
    start_minute = 15
    end_hour = 22
    end_minute = 15
    slot_duration_minutes = 45

    slots = []
    current_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    # We want to include the end time slot
    end_time = datetime.now().replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

    while current_time <= end_time:
        slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=slot_duration_minutes)
    return slots


def test_parsing():
    # User provided JSON sample
    json_data = """
    {"slots":[{"date":"2025-11-05","start":"1100","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1230","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1445","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1615","court":77394,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1615","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1615","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1700","court":77394,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1700","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1700","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1745","court":77394,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1745","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1745","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1830","court":77394,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1830","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1830","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1915","court":77394,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1915","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"1915","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"2000","court":77394,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"2000","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"2000","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"2045","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"2045","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"2130","court":77395,"title":null,"present":true,"isUserBookingOwner":false,"booking":null},{"date":"2025-11-05","start":"2130","court":77396,"title":null,"present":true,"isUserBookingOwner":false,"booking":null}]}
    """
    data = json.loads(json_data)

    # Test date from the JSON
    date_str = "2025-11-05"

    all_slots = get_all_slots()
    print(f"All possible slots: {all_slots}")

    booked_counts = {slot: 0 for slot in all_slots}

    for booking in data["slots"]:
        if booking.get("date") == date_str:
            start_raw = booking.get("start")  # e.g., "1100"
            if start_raw:
                start_formatted = f"{start_raw[:2]}:{start_raw[2:]}"
                if start_formatted in booked_counts:
                    booked_counts[start_formatted] += 1
                else:
                    print(f"Warning: Booked slot {start_formatted} not in generated slots!")

    total_courts = len(COURT_IDS)
    free_slots = []

    print(f"\n--- Availability Report for {date_str} ---")
    for slot in all_slots:
        booked = booked_counts.get(slot, 0)
        available = total_courts - booked
        if available > 0:
            free_slots.append(slot)
            print(f"[AVAILABLE] {slot}: {available} court(s) free")
        else:
            print(f"[FULL]      {slot}: 0 courts free")

    print(f"\nSummary: Found {len(free_slots)} available time slots!")


if __name__ == "__main__":
    test_parsing()
