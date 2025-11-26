from unittest.mock import MagicMock, patch

from eversports_scraper import run
from eversports_scraper.models import DayAvailability, Slot, TargetDate


@patch("eversports_scraper.run.requests.get")
def test_fetch_target_dates_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "21.11.2025\n23.11.2025"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    dates = run.fetch_target_dates("http://fake.url")
    assert len(dates) == 2
    assert dates[0].date == "2025-11-21"
    assert dates[1].date == "2025-11-23"
    assert dates[0].start_time is None
    assert dates[0].end_time is None


@patch("eversports_scraper.run.requests.get")
def test_fetch_target_dates_failure(mock_get):
    mock_get.side_effect = Exception("Network error")
    dates = run.fetch_target_dates("http://fake.url")
    assert dates == []


@patch("eversports_scraper.run.requests.get")
def test_fetch_target_dates_with_header(mock_get):
    """Test parsing CSV with header row."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Date,Start,End\n21.11.2025,10:00,14:00\n23.11.2025,15:30,18:45"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    dates = run.fetch_target_dates("http://fake.url")
    # Should skip the header and parse only the 2 data rows
    assert len(dates) == 2
    assert dates[0].date == "2025-11-21"
    assert dates[0].start_time == "10:00"


@patch("eversports_scraper.run.requests.get")
def test_fetch_target_dates_with_times(mock_get):
    """Test parsing CSV with time intervals."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "21.11.2025,10:00,14:00\n23.11.2025,15:30,18:45"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    dates = run.fetch_target_dates("http://fake.url")
    assert len(dates) == 2
    assert dates[0].date == "2025-11-21"
    assert dates[0].start_time == "10:00"
    assert dates[0].end_time == "14:00"
    assert dates[1].date == "2025-11-23"
    assert dates[1].start_time == "15:30"
    assert dates[1].end_time == "18:45"


@patch("eversports_scraper.run.requests.get")
def test_fetch_target_dates_partial_times(mock_get):
    """Test parsing CSV with missing time values."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "21.11.2025,10:00,\n23.11.2025,,14:00"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    dates = run.fetch_target_dates("http://fake.url")
    assert len(dates) == 2
    assert dates[0].start_time == "10:00"
    assert dates[0].end_time is None
    assert dates[1].start_time is None
    assert dates[1].end_time == "14:00"


def test_check_time_overlap_within_range():
    """Test slot fully within interval."""
    target = TargetDate(date="2025-01-01", start_time="10:00", end_time="14:00")
    assert run.check_time_overlap("11:00", target) is True
    assert run.check_time_overlap("10:15", target) is True
    assert run.check_time_overlap("13:00", target) is True


def test_check_time_overlap_partial():
    """Test slot partially overlaps interval."""
    target = TargetDate(date="2025-01-01", start_time="10:00", end_time="11:00")
    # Slot 10:15-11:00 overlaps with 10:00-11:00
    assert run.check_time_overlap("10:15", target) is True
    # Slot 10:30-11:15 overlaps with 10:00-11:00 (ends after interval)
    assert run.check_time_overlap("10:30", target) is True


def test_check_time_overlap_outside():
    """Test slot outside interval."""
    target = TargetDate(date="2025-01-01", start_time="10:00", end_time="11:00")
    # Slot 11:00-11:45 starts exactly when interval ends
    assert run.check_time_overlap("11:00", target) is False
    # Slot 09:00-09:45 ends before interval starts
    assert run.check_time_overlap("09:00", target) is False
    # Slot 14:00-14:45 is way outside
    assert run.check_time_overlap("14:00", target) is False


def test_check_time_overlap_no_interval():
    """Test behavior when no interval is specified."""
    target = TargetDate(date="2025-01-01", start_time=None, end_time=None)
    assert run.check_time_overlap("10:00", target) is True
    assert run.check_time_overlap("18:00", target) is True
    
    # Partial interval (only start or only end) should also return True
    target_partial = TargetDate(date="2025-01-01", start_time="10:00", end_time=None)
    assert run.check_time_overlap("11:00", target_partial) is True


@patch("eversports_scraper.run.fetch_target_dates")
@patch("eversports_scraper.run.scraper.get_all_slots")
@patch("eversports_scraper.run.scraper.get_day_availability")
@patch("eversports_scraper.run.telegram_notifier.send_telegram_message")
@patch("eversports_scraper.run.persist.save_history")
@patch("eversports_scraper.run.persist.save_report")
@patch("eversports_scraper.run.persist.load_history")
def test_main_flow(
    mock_load_history,
    mock_save_report,
    mock_save_history,
    mock_send_telegram,
    mock_get_day,
    mock_get_slots,
    mock_fetch_dates,
):
    # Setup mocks
    mock_fetch_dates.return_value = [TargetDate(date="2025-01-01", start_time=None, end_time=None)]
    mock_get_slots.return_value = ["10:00"]
    mock_load_history.return_value = {}

    # Mock return for get_day_availability
    # Return a day with new slots to trigger telegram
    mock_get_day.return_value = DayAvailability(
        date="2025-01-01",
        slots=[Slot(time="10:00", courts=["Court 1"], court_ids=[77394], is_new=True)],
        new_count=1,
        free_slots_map={"10:00": [77394]},
    )

    with patch("eversports_scraper.run.config.TARGET_DATES_CSV_URL", "http://mock.url"):
        run.run(start_date=None, days=3)

        mock_fetch_dates.assert_called_once()
        mock_get_slots.assert_called_once()
        mock_get_day.assert_called()
        mock_load_history.assert_called()
        mock_save_history.assert_called()
        mock_save_report.assert_called()
        mock_send_telegram.assert_called_once()


@patch("eversports_scraper.run.fetch_target_dates")
@patch("eversports_scraper.run.scraper.get_all_slots")
@patch("eversports_scraper.run.scraper.get_day_availability")
@patch("eversports_scraper.run.telegram_notifier.send_telegram_message")
@patch("eversports_scraper.run.persist.save_history")
@patch("eversports_scraper.run.persist.save_report")
@patch("eversports_scraper.run.persist.load_history")
def test_main_flow_manual_override(
    mock_load_history,
    mock_save_report,
    mock_save_history,
    mock_send_telegram,
    mock_get_day,
    mock_get_slots,
    mock_fetch_dates,
):
    # Setup mocks
    mock_load_history.return_value = {}
    mock_get_slots.return_value = ["10:00"]
    mock_get_day.return_value = None  # No data found
    mock_fetch_dates.return_value = []  # Empty CSV to trigger fallback

    with patch("eversports_scraper.run.config.TARGET_DATES_CSV_URL", "http://mock.url"):
        run.run(start_date="2025-01-01", days=1)

        # Should fetch from CSV
        mock_fetch_dates.assert_called_once()

        # Should call scraper for the manual date (fallback)
        mock_get_day.assert_called_with("2025-01-01", ["10:00"], {})


@patch("eversports_scraper.run.fetch_target_dates")
@patch("eversports_scraper.run.scraper.get_all_slots")
@patch("eversports_scraper.run.scraper.get_day_availability")
@patch("eversports_scraper.run.telegram_notifier.send_telegram_message")
@patch("eversports_scraper.run.persist.save_history")
@patch("eversports_scraper.run.persist.save_report")
@patch("eversports_scraper.run.persist.load_history")
def test_main_flow_csv_fallback(
    mock_load_history,
    mock_save_report,
    mock_save_history,
    mock_send_telegram,
    mock_get_day,
    mock_get_slots,
    mock_fetch_dates,
):
    # Setup mocks
    mock_load_history.return_value = {}
    mock_get_slots.return_value = ["10:00"]
    mock_get_day.return_value = None
    mock_fetch_dates.return_value = []  # Empty CSV

    with patch("eversports_scraper.run.config.TARGET_DATES_CSV_URL", "http://mock.url"):
        run.run(start_date=None, days=3)

        # Should fetch from CSV
        mock_fetch_dates.assert_called_once()

        # Should fall back to 3 days
        assert mock_get_day.call_count == 3


@patch("eversports_scraper.run.fetch_target_dates")
@patch("eversports_scraper.run.scraper.get_all_slots")
@patch("eversports_scraper.run.scraper.get_day_availability")
@patch("eversports_scraper.run.telegram_notifier.send_telegram_message")
def test_main_no_new_slots(mock_send_telegram, mock_get_day, mock_get_slots, mock_fetch_dates):
    mock_fetch_dates.return_value = [TargetDate(date="2025-01-01", start_time=None, end_time=None)]
    mock_get_slots.return_value = ["10:00"]
    mock_get_day.return_value = DayAvailability(
        date="2025-01-01",
        slots=[Slot(time="10:00", courts=["Court 1"], court_ids=[77394], is_new=False)],
        new_count=0,
        free_slots_map={"10:00": [77394]},
    )

    run.run(start_date=None, days=3)

    mock_send_telegram.assert_not_called()


@patch("eversports_scraper.run.fetch_target_dates")
@patch("eversports_scraper.run.scraper.get_all_slots")
@patch("eversports_scraper.run.scraper.get_day_availability")
@patch("eversports_scraper.run.telegram_notifier.send_telegram_message")
@patch("eversports_scraper.run.persist.save_history")
@patch("eversports_scraper.run.persist.save_report")
@patch("eversports_scraper.run.persist.load_history")
def test_notification_filtered_by_time(
    mock_load_history,
    mock_save_report,
    mock_save_history,
    mock_send_telegram,
    mock_get_day,
    mock_get_slots,
    mock_fetch_dates,
):
    """Test that notifications only include slots within the time interval."""
    # Set up a target date with time interval 10:00-12:00
    mock_fetch_dates.return_value = [
        TargetDate(date="2025-01-01", start_time="10:00", end_time="12:00")
    ]
    mock_get_slots.return_value = ["10:15", "11:00", "14:00"]
    mock_load_history.return_value = {}

    # Return availability with new slots at 10:15, 11:00, and 14:00
    mock_get_day.return_value = DayAvailability(
        date="2025-01-01",
        slots=[
            Slot(time="10:15", courts=["Court 1"], court_ids=[77394], is_new=True),
            Slot(time="11:00", courts=["Court 2"], court_ids=[77395], is_new=True),
            Slot(time="14:00", courts=["Court 3"], court_ids=[77396], is_new=True),
        ],
        new_count=3,
        free_slots_map={"10:15": [77394], "11:00": [77395], "14:00": [77396]},
    )

    with patch("eversports_scraper.run.config.TARGET_DATES_CSV_URL", "http://mock.url"):
        run.run(start_date=None, days=3)

        # Should send telegram
        mock_send_telegram.assert_called_once()
        
        # Check the message content - should only include 10:15 and 11:00, not 14:00
        message = mock_send_telegram.call_args[0][0]
        assert "10:15" in message
        assert "11:00" in message
        assert "14:00" not in message

