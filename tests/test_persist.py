from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

from eversports_scraper import config, persist
from eversports_scraper.models import DayAvailability


def test_ensure_data_dir():
    with patch("os.path.exists") as mock_exists, patch("os.makedirs") as mock_makedirs:
        # Case 1: Exists
        mock_exists.return_value = True
        persist.ensure_data_dir()
        mock_makedirs.assert_not_called()

        # Case 2: Does not exist
        mock_exists.return_value = False
        persist.ensure_data_dir()
        mock_makedirs.assert_called_with(config.DATA_DIR)




@patch("eversports_scraper.persist.config.HISTORY_FILE", "/tmp/test_history.json")
@patch("os.path.exists")
def test_load_history(mock_exists):
    """Test loading history with new timestamp format."""
    mock_exists.return_value = True
    test_data = '{"last_updated": "2025-01-01T12:00:00Z", "availability": {"2025-01-01": {}}}'
    with patch("builtins.open", mock_open(read_data=test_data)):
        history = persist.load_history()
        assert history == {"2025-01-01": {}}




@patch("eversports_scraper.persist.config.HISTORY_FILE", "/tmp/test_history_legacy.json")
@patch("os.path.exists")
def test_load_history_legacy_format(mock_exists):
    """Test loading history with legacy format (no timestamp)."""
    mock_exists.return_value = True
    test_data = '{"2025-01-01": {}}'
    with patch("builtins.open", mock_open(read_data=test_data)):
        history = persist.load_history()
        assert history == {"2025-01-01": {}}


def test_load_history_no_file():
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False
        history = persist.load_history()
        assert history == {}


@patch("eversports_scraper.persist.datetime")
@patch("eversports_scraper.persist.json.dump")
@patch("eversports_scraper.persist.ensure_data_dir")
def test_save_history(mock_ensure, mock_dump, mock_datetime):
    """Test that save_history wraps data with timestamp."""
    # Mock datetime to return a consistent timestamp
    mock_now = MagicMock()
    mock_now.isoformat.return_value = "2025-01-01T12:00:00Z"
    mock_datetime.now.return_value = mock_now
    
    with patch("builtins.open", mock_open()):
        history = {"test": "data"}
        persist.save_history(history)

        # Check that json.dump was called with wrapped data
        args, _ = mock_dump.call_args
        saved_data = args[0]
        assert "last_updated" in saved_data
        assert "availability" in saved_data
        assert saved_data["availability"] == history
        assert saved_data["last_updated"] == "2025-01-01T12:00:00Z"


def test_save_report():
    with patch("eversports_scraper.persist.ensure_data_dir"), patch("builtins.open", mock_open()):
        results = [DayAvailability(date="2025-01-01", slots=[], new_count=0, free_slots_map={})]
        persist.save_report(results)


@patch("eversports_scraper.persist.json.dump")
def test_save_report_structure(mock_dump):
    with patch("eversports_scraper.persist.ensure_data_dir"), patch("builtins.open", mock_open()):
        results = [DayAvailability(date="2025-01-01", slots=[], new_count=0, free_slots_map={})]
        persist.save_report(results)

        args, _ = mock_dump.call_args
        data = args[0]
        assert "last_updated" in data
        datetime.fromisoformat(data["last_updated"])
        assert "days" in data
        assert data["days"][0]["date"] == "2025-01-01"
