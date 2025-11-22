import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import requests

# Add parent directory to path to import telegram_notifier
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import telegram_notifier

@patch('os.environ.get')
@patch('telegram_notifier.requests.post')
def test_send_telegram_message_success(mock_post, mock_env):
    # Setup env
    def env_side_effect(key):
        if key == "TELEGRAM_BOT_TOKEN": return "fake_token"
        if key == "TELEGRAM_CHAT_ID": return "fake_chat_id"
        return None
    mock_env.side_effect = env_side_effect
    
    # Setup response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    telegram_notifier.send_telegram_message("Test message")
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.telegram.org/botfake_token/sendMessage"
    assert kwargs["json"]["chat_id"] == "fake_chat_id"
    assert kwargs["json"]["text"] == "Test message"

@patch('os.environ.get')
@patch('telegram_notifier.requests.post')
def test_send_telegram_message_missing_config(mock_post, mock_env):
    mock_env.return_value = None # No env vars
    
    telegram_notifier.send_telegram_message("Test message")
    
    mock_post.assert_not_called()

@patch('os.environ.get')
@patch('telegram_notifier.requests.post')
def test_send_telegram_message_failure(mock_post, mock_env):
    # Setup env
    mock_env.return_value = "fake"
    
    # Setup failure
    mock_post.side_effect = requests.exceptions.RequestException("Network error")
    
    # Should log error but not crash
    telegram_notifier.send_telegram_message("Test message")
    
    mock_post.assert_called_once()
