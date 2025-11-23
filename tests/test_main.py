from unittest.mock import MagicMock, patch

from eversports_scraper import main as main_module


@patch("eversports_scraper.main.requests.get")
def test_fetch_target_dates_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "21.11.2025\n23.11.2025"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    dates = main_module.fetch_target_dates("http://fake.url")
    assert dates == ["2025-11-21", "2025-11-23"]


@patch("eversports_scraper.main.requests.get")
def test_fetch_target_dates_failure(mock_get):
    mock_get.side_effect = Exception("Network error")
    dates = main_module.fetch_target_dates("http://fake.url")
    assert dates == []


@patch("eversports_scraper.main.fetch_target_dates")
@patch("eversports_scraper.main.scraper.get_all_slots")
@patch("eversports_scraper.main.scraper.get_day_availability")
@patch("eversports_scraper.main.telegram_notifier.send_telegram_message")
@patch("eversports_scraper.main.persist.save_history")
@patch("eversports_scraper.main.persist.save_report")
@patch("eversports_scraper.main.persist.load_history")
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
    mock_fetch_dates.return_value = ["2025-01-01"]
    mock_get_slots.return_value = ["10:00"]
    mock_load_history.return_value = {}

    # Mock return for get_day_availability
    # Return a day with new slots to trigger telegram
    mock_get_day.return_value = {
        "date": "2025-01-01",
        "slots": [{"time": "10:00", "courts": ["Court 1"], "is_new": True}],
        "new_count": 1,
        "free_slots_map": {"10:00": [77394]},
    }

    with patch("eversports_scraper.main.parse_arguments") as mock_args:
        mock_args.return_value = MagicMock(verbose=False)

        main_module.main()

        mock_fetch_dates.assert_called_once()
        mock_get_slots.assert_called_once()
        mock_get_day.assert_called()
        mock_load_history.assert_called()
        mock_save_history.assert_called()
        mock_save_report.assert_called()
        mock_send_telegram.assert_called_once()


@patch("eversports_scraper.main.fetch_target_dates")
@patch("eversports_scraper.main.scraper.get_all_slots")
@patch("eversports_scraper.main.scraper.get_day_availability")
@patch("eversports_scraper.main.telegram_notifier.send_telegram_message")
@patch("eversports_scraper.main.persist.save_history")
@patch("eversports_scraper.main.persist.save_report")
@patch("eversports_scraper.main.persist.load_history")
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

    with patch("eversports_scraper.main.parse_arguments") as mock_args:
        # Simulate CLI args
        mock_args.return_value = MagicMock(start_date="2025-01-01", days=1, verbose=False)

        main_module.main()

        # Should fetch from CSV# No changes needed yet, let's verify first.)
        mock_fetch_dates.assert_called_once()

        # Should call scraper for the manual date (fallback)
        mock_get_day.assert_called_with("2025-01-01", ["10:00"], {})


@patch("eversports_scraper.main.fetch_target_dates")
@patch("eversports_scraper.main.scraper.get_all_slots")
@patch("eversports_scraper.main.scraper.get_day_availability")
@patch("eversports_scraper.main.telegram_notifier.send_telegram_message")
@patch("eversports_scraper.main.persist.save_history")
@patch("eversports_scraper.main.persist.save_report")
@patch("eversports_scraper.main.persist.load_history")
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

    with patch("eversports_scraper.main.parse_arguments") as mock_args:
        # No CLI args
        mock_args.return_value = MagicMock(start_date=None, days=3, verbose=False)

        main_module.main()

        # Should fetch from CSV
        mock_fetch_dates.assert_called_once()

        # Should fall back to 3 days
        assert mock_get_day.call_count == 3


@patch("eversports_scraper.main.fetch_target_dates")
@patch("eversports_scraper.main.scraper.get_all_slots")
@patch("eversports_scraper.main.scraper.get_day_availability")
@patch("eversports_scraper.main.telegram_notifier.send_telegram_message")
def test_main_no_new_slots(mock_send_telegram, mock_get_day, mock_get_slots, mock_fetch_dates):
    mock_fetch_dates.return_value = ["2025-01-01"]
    mock_get_slots.return_value = ["10:00"]
    mock_get_day.return_value = {
        "date": "2025-01-01",
        "slots": [{"time": "10:00", "courts": ["Court 1"], "is_new": False}],
        "new_count": 0,
        "free_slots_map": {"10:00": [77394]},
    }

    with patch("eversports_scraper.main.parse_arguments") as mock_args:
        mock_args.return_value = MagicMock(start_date=None, verbose=False)

        main_module.main()

        mock_send_telegram.assert_not_called()
