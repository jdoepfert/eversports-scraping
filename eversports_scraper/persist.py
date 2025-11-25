import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List

from eversports_scraper import config

logger = logging.getLogger(__name__)


def ensure_data_dir():
    """Ensures the data directory exists."""
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR)


def load_history() -> Dict:
    """Loads the previous availability state from a JSON file with timestamp metadata."""
    if not os.path.exists(config.HISTORY_FILE):
        logger.info("No history file found. Starting fresh.")
        return {}
    try:
        with open(config.HISTORY_FILE, "r") as f:
            data: Dict = json.load(f)
            # Expect new format with timestamp
            if "last_updated" in data and "availability" in data:
                logger.info(f"Loaded history from cache, last updated: {data['last_updated']}")
                return data["availability"]
            else:
                logger.warning("History file has unexpected format. Starting fresh.")
                return {}
    except (json.JSONDecodeError, IOError):
        logger.warning("Failed to load history file. Starting fresh.")
        return {}


def save_history(history: Dict):
    """Saves the current availability state to a JSON file with timestamp."""
    ensure_data_dir()
    try:
        # Wrap history with metadata
        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "availability": history
        }
        with open(config.HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved history to {config.HISTORY_FILE} on {data['last_updated']}")
    except IOError as e:
        logger.error(f"Failed to save history: {e}")


def save_report(results: List):
    """Saves the availability report to a JSON file."""
    ensure_data_dir()
    try:
        # Convert Pydantic models to dicts if necessary
        serialized_results = [r.model_dump() if hasattr(r, "model_dump") else r for r in results]
        data = {"last_updated": datetime.now(timezone.utc).isoformat(), "days": serialized_results}
        with open(config.REPORT_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved report to {config.REPORT_FILE}")
    except IOError as e:
        logger.error(f"Failed to save report: {e}")
