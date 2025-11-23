import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import requests

# Add parent directory to path to import telegram_notifier
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eversports_scraper import telegram_notifier

@patch('eversports_scraper.telegram_notifier.requests.post')
@patch('eversports_scraper.telegram_notifier.config')
def test_send_telegram_message_success(mock_config, mock_post):
    mock_config.TELEGRAM_BOT_TOKEN = "fake_token"
    mock_config.TELEGRAM_CHAT_ID = "fake_chat_id"
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    telegram_notifier.send_telegram_message("Test message")
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs['json']['text'] == "Test message"
    assert "fake_token" in args[0]

@patch('eversports_scraper.telegram_notifier.requests.post')
@patch('eversports_scraper.telegram_notifier.config')
def test_send_telegram_message_missing_config(mock_config, mock_post):
    mock_config.TELEGRAM_BOT_TOKEN = None
    mock_config.TELEGRAM_CHAT_ID = None
    
    telegram_notifier.send_telegram_message("Test message")
    
    mock_post.assert_not_called()

@patch('eversports_scraper.telegram_notifier.requests.post')
@patch('eversports_scraper.telegram_notifier.config')
def test_send_telegram_message_failure(mock_config, mock_post):
    mock_config.TELEGRAM_BOT_TOKEN = "fake_token"
    mock_config.TELEGRAM_CHAT_ID = "fake_chat_id"
    
    mock_post.side_effect = requests.exceptions.RequestException("Network error")
    
    # Should not raise exception, just log error
    telegram_notifier.send_telegram_message("Test message")
    
    mock_post.assert_called_once()
