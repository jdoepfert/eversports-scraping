# Eversports Scraping

![CI Status](https://github.com/jdoepfert/eversports-scraping/actions/workflows/ci.yml/badge.svg)

A Python scraper to monitor badminton court availability on Eversports for Squash House in Berlin.

## Features
- Scrapes availability for specified dates (configured via Google Sheet).
- Sends Telegram notifications for new slots.
- Generates a static availability report.
- Automated regular scraping via GitHub Actions.

## Configuration

Before running the scraper, you need to set up the following:

### 1. Google Sheet with Target Dates

Create a Google Sheet to specify which dates and times you want to monitor:

1. Create a new Google Sheet with the following structure:
   - **Column A**: Date in `YYYY-MM-DD` format (e.g., `2025-11-26`)
   - **Column B**: Start time for filtering in `HH:MM` format (e.g., `18:00`)
   - **Column C**: End time for filtering in `HH:MM` format (e.g., `20:00`)
   
2. Optionally add a header row (it will be skipped automatically)

3. Publish the sheet as CSV:
   - Go to **File** → **Share** → **Publish to web**
   - Select the specific sheet/tab
   - Choose **Comma-separated values (.csv)** as the format
   - Click **Publish** and copy the generated URL

### 2. Telegram Bot Setup

Create a Telegram bot to receive notifications:

1. **Create a bot:**
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow the instructions
   - Copy the **bot token** provided (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

2. **Get the Chat ID:**
   - Create a Telegram channel or group where you want to receive notifications
   - Add your bot to the channel/group as an administrator
   - Send a test message in the channel/group
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in your browser
   - Look for the `"chat":{"id":...}` field in the response
   - Copy the chat ID (it's usually a negative number for groups/channels)

### 3. Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
TARGET_DATES_CSV_URL="<your-google-sheet-csv-url>"
TELEGRAM_BOT_TOKEN="<your-bot-token>"
TELEGRAM_CHAT_ID="<your-chat-id>"
```

Example:
```bash
TARGET_DATES_CSV_URL="https://docs.google.com/spreadsheets/d/e/2PACX-1vSexample/pub?output=csv"
TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
TELEGRAM_CHAT_ID="-1001234567890"
```

## Running Locally

### Prerequisites
- Python 3.10+
- Configured `.env` file (see [Configuration](#configuration) section above)

### Installation
```bash
make install
```

### Run Scraper
```bash
make run
```

This will use the dates from your Google Sheet CSV to check for availability.

### CLI Options

The scraper can also be run directly with custom options:

```bash
# Run with default settings (uses Google Sheet dates or today + 3 days)
python -m eversports_scraper

# Specify a start date and number of days to check
python -m eversports_scraper --start-date 2025-11-26 --days 5

```

**CLI Arguments:**
- `--start-date`: Start date in `YYYY-MM-DD` format (defaults to today)
- `--days`: Number of days to check from start date (default: 3)
- `-v, --verbose`: Enable verbose/debug logging

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
