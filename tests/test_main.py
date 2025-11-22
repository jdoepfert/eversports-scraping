import pytest
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch, mock_open

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"slots": []}
    return mock

@pytest.fixture
def mock_scraper(mock_response):
    scraper = MagicMock()
    scraper.get.return_value = mock_response
    return scraper

def test_get_all_slots():
    slots = main.get_all_slots()
    assert len(slots) > 0
    assert "10:15" in slots
    assert "22:15" in slots
    # Check interval
    fmt = "%H:%M"
    t1 = datetime.strptime(slots[0], fmt)
    t2 = datetime.strptime(slots[1], fmt)
    assert (t2 - t1).seconds == 45 * 60

def test_build_url():
    date = "2025-01-01"
    url = main.build_url(date)
    assert main.API_BASE in url
    assert f"startDate={date}" in url
    assert "facilityId=76443" in url
    for cid in main.COURT_IDS:
        assert f"courts%5B%5D={cid}" in url

@patch('main.cloudscraper.create_scraper')
def test_fetch_booked_slots_success(mock_create_scraper, mock_scraper):
    mock_create_scraper.return_value = mock_scraper
    data = main.fetch_booked_slots("2025-01-01")
    assert data == {"slots": []}
    mock_scraper.get.assert_called_once()

@patch('main.cloudscraper.create_scraper')
def test_fetch_booked_slots_failure(mock_create_scraper, mock_scraper):
    mock_create_scraper.return_value = mock_scraper
    mock_scraper.get.side_effect = Exception("Network error")
    data = main.fetch_booked_slots("2025-01-01")
    assert data is None

def test_parse_booked_slots():
    all_slots = ["10:15", "11:00"]
    date_str = "2025-01-01"
    data = {
        "slots": [
            {"date": "2025-01-01", "start": "1015", "court": 123},
            {"date": "2025-01-01", "start": "1100", "court": 456},
            {"date": "2025-01-02", "start": "1015", "court": 789} # Wrong date
        ]
    }
    
    result = main.parse_booked_slots(data, date_str, all_slots)
    
    assert 123 in result["10:15"]
    assert 456 in result["11:00"]
    assert len(result["10:15"]) == 1

def test_ensure_data_dir():
    with patch('os.path.exists') as mock_exists, \
         patch('os.makedirs') as mock_makedirs:
        
        # Case 1: Exists
        mock_exists.return_value = True
        main.ensure_data_dir()
        mock_makedirs.assert_not_called()
        
        # Case 2: Does not exist
        mock_exists.return_value = False
        main.ensure_data_dir()
        mock_makedirs.assert_called_with(main.DATA_DIR)

def test_load_history():
    with patch('os.path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data='{"2025-01-01": {}}')):
        
        mock_exists.return_value = True
        history = main.load_history()
        assert history == {"2025-01-01": {}}

def test_load_history_no_file():
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False
        history = main.load_history()
        assert history == {}

def test_save_history():
    with patch('main.ensure_data_dir'), \
         patch('builtins.open', mock_open()) as mock_file:
        
        history = {"test": "data"}
        main.save_history(history)
        
        handle = mock_file()
        # Check if json.dump was called (write was called on file handle)
        assert handle.write.called

def test_calculate_free_slots():
    all_slots = ["10:00"]
    # Assume COURT_IDS are [77394, 77395, 77396]
    booked = {"10:00": {77394, 77395}}
    
    free = main.calculate_free_slots(booked, all_slots)
    
    assert "10:00" in free
    assert len(free["10:00"]) == 1
    assert 77396 in free["10:00"]

@patch('main.fetch_booked_slots')
def test_get_day_availability(mock_fetch):
    # Mock data
    mock_fetch.return_value = {
        "slots": [
            {"date": "2025-01-01", "start": "1015", "court": 77394}
        ]
    }
    
    all_slots = ["10:15"]
    history = {} # No history
    
    # Assume COURT_IDS has 3 courts, 1 booked -> 2 free
    result = main.get_day_availability("2025-01-01", all_slots, history)
    
    assert result["date"] == "2025-01-01"
    assert len(result["slots"]) == 1
    assert result["slots"][0]["time"] == "10:15"
    assert len(result["slots"][0]["court_ids"]) == 2
    assert result["new_count"] > 0 # Since history was empty, these are new

def test_save_report():
    with patch('main.ensure_data_dir'), \
         patch('builtins.open', mock_open()) as mock_file:
        
        results = [{"date": "2025-01-01"}]
        main.save_report(results)
        
        handle = mock_file()
        # Get the arguments passed to write
        # json.dump writes in chunks, so we might need to capture all writes or just check call args
        # Easier to mock json.dump
        pass

@patch('main.json.dump')
def test_save_report_structure(mock_dump):
    with patch('main.ensure_data_dir'), \
         patch('builtins.open', mock_open()):
        
        results = [{"date": "2025-01-01"}]
        main.save_report(results)
        
        # Check what was passed to json.dump
        args, _ = mock_dump.call_args
        data = args[0]
        assert "last_updated" in data
        assert "days" in data
        assert data["days"] == results
