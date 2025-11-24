from datetime import datetime
from unittest.mock import mock_open, patch

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


def test_load_history():
    with patch("os.path.exists") as mock_exists, patch("builtins.open", mock_open(read_data='{"2025-01-01": {}}')):
        mock_exists.return_value = True
        history = persist.load_history()
        assert history == {"2025-01-01": {}}


def test_load_history_no_file():
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False
        history = persist.load_history()
        assert history == {}


def test_save_history():
    with patch("eversports_scraper.persist.ensure_data_dir"), patch("builtins.open", mock_open()) as mock_file:
        history = {"test": "data"}
        persist.save_history(history)

        handle = mock_file()
        assert handle.write.called


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
