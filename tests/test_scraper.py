import pytest
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add parent directory to path to import scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scraper

@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"slots": []}
    return mock

@pytest.fixture
def mock_scraper_obj(mock_response):
    s = MagicMock()
    s.get.return_value = mock_response
    return s

def test_get_all_slots():
    slots = scraper.get_all_slots()
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
    url = scraper.build_url(date)
    assert scraper.API_BASE in url
    assert f"startDate={date}" in url
    assert "facilityId=76443" in url
    for cid in scraper.COURT_IDS:
        assert f"courts%5B%5D={cid}" in url

@patch('scraper.cloudscraper.create_scraper')
def test_fetch_booked_slots_success(mock_create_scraper, mock_scraper_obj):
    mock_create_scraper.return_value = mock_scraper_obj
    data = scraper.fetch_booked_slots("2025-01-01")
    assert data == {"slots": []}
    mock_scraper_obj.get.assert_called_once()

@patch('scraper.cloudscraper.create_scraper')
def test_fetch_booked_slots_failure(mock_create_scraper, mock_scraper_obj):
    mock_create_scraper.return_value = mock_scraper_obj
    mock_scraper_obj.get.side_effect = Exception("Network error")
    data = scraper.fetch_booked_slots("2025-01-01")
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
    
    result = scraper.parse_booked_slots(data, date_str, all_slots)
    
    assert 123 in result["10:15"]
    assert 456 in result["11:00"]
    assert len(result["10:15"]) == 1

def test_calculate_free_slots():
    all_slots = ["10:00"]
    # Assume COURT_IDS are [77394, 77395, 77396]
    booked = {"10:00": {77394, 77395}}
    
    free = scraper.calculate_free_slots(booked, all_slots)
    
    assert "10:00" in free
    assert len(free["10:00"]) == 1
    assert 77396 in free["10:00"]

@patch('scraper.fetch_booked_slots')
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
    result = scraper.get_day_availability("2025-01-01", all_slots, history)
    
    assert result["date"] == "2025-01-01"
    assert len(result["slots"]) == 1
    assert result["slots"][0]["time"] == "10:15"
    assert len(result["slots"][0]["court_ids"]) == 2
    assert result["new_count"] > 0 # Since history was empty, these are new
