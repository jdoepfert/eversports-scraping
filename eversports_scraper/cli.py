import argparse
import logging
import sys

from eversports_scraper import run

# --- Logging Setup ---

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool):
    """Configures logging to stderr with local time."""
    import time
    
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s]: %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Use local time instead of UTC for logging
    formatter.converter = time.localtime
    handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=level,
        handlers=[handler],
    )


def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Scrape Eversports for free badminton courts.")
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--days", type=int, default=3, help="Number of days to check. Defaults to 3.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def main():
    args = parse_arguments()
    setup_logging(args.verbose)
    run.run(start_date=args.start_date, days=args.days)
