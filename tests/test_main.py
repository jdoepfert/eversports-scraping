import pytest
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch, mock_open

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

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
        assert handle.write.called

def test_save_report():
    with patch('main.ensure_data_dir'), \
         patch('builtins.open', mock_open()):
        
        results = [{"date": "2025-01-01"}]
        main.save_report(results)

@patch('main.json.dump')
def test_save_report_structure(mock_dump):
    with patch('main.ensure_data_dir'), \
         patch('builtins.open', mock_open()):
        
        results = [{"date": "2025-01-01"}]
        main.save_report(results)
        
        args, _ = mock_dump.call_args
        data = args[0]
        assert "last_updated" in data
        datetime.fromisoformat(data["last_updated"])
        assert "days" in data
        assert data["days"] == results

@patch('main.scraper.get_all_slots')
@patch('main.scraper.get_day_availability')
@patch('main.telegram_notifier.send_telegram_message')
@patch('main.save_history')
@patch('main.save_report')
def test_main_flow(mock_save_report, mock_save_history, mock_send_telegram, mock_get_day, mock_get_slots):
    # Setup mocks
    mock_get_slots.return_value = ["10:00"]
    
    # Mock return for get_day_availability
    # Return a day with new slots to trigger telegram
    mock_get_day.return_value = {
        "date": "2025-01-01",
        "slots": [{"time": "10:00", "courts": ["Court 1"], "is_new": True}],
        "new_count": 1,
        "free_slots_map": {"10:00": [77394]}
    }
    
    # Mock args
    with patch('main.parse_arguments') as mock_args:
        mock_args.return_value = MagicMock(start_date=None, days=1, verbose=False)
        
        main.main()
        
        mock_get_slots.assert_called_once()
        mock_get_day.assert_called()
        mock_save_history.assert_called()
        mock_save_report.assert_called()
        mock_send_telegram.assert_called_once()

@patch('main.scraper.get_all_slots')
@patch('main.scraper.get_day_availability')
@patch('main.telegram_notifier.send_telegram_message')
def test_main_no_new_slots(mock_send_telegram, mock_get_day, mock_get_slots):
    mock_get_slots.return_value = ["10:00"]
    mock_get_day.return_value = {
        "date": "2025-01-01",
        "slots": [{"time": "10:00", "courts": ["Court 1"], "is_new": False}],
        "new_count": 0,
        "free_slots_map": {"10:00": [77394]}
    }
    
    with patch('main.parse_arguments') as mock_args:
        mock_args.return_value = MagicMock(start_date=None, days=1, verbose=False)
        
        main.main()
        
        mock_send_telegram.assert_not_called()
