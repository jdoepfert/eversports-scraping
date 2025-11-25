# Eversports Scraping

![CI Status](https://github.com/jdoepfert/eversports-scraping/actions/workflows/ci.yml/badge.svg)

A Python scraper to monitor badminton court availability on Eversports for Squash House in Berlin.

## Features
- Scrapes availability for specified dates (configured via Google Sheet).
- Sends Telegram notifications for new slots.
- Generates a static availability report.
- Automated regular scraping via GitHub Actions.

## Running Locally

### Prerequisites
- Python 3.10+
- The folowing environment variables or a `.env` file with the following variables:
  ```bash
  TARGET_DATES_CSV_URL="<url-to-google-sheet-csv>"
  TELEGRAM_BOT_TOKEN="<your-bot-token>"
  TELEGRAM_CHAT_ID="<your-chat-id>"
  ```

### Installation
```bash
make install
```

### Run Scraper
```bash
make run
```

## Development

### Setup
```bash
make install-dev
```

### Running Tests
```bash
make test
```

### Linting & Type Checking
```bash
make lint
make type-check
```
