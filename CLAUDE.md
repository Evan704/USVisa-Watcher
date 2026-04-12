# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based visa appointment monitoring tool that scrapes qmq.app for US visa appointment availability and sends email notifications when earlier dates become available.

## Common Commands

### Environment Setup
```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate visa-scraper

# Install browser for Playwright
playwright install chromium
```

### Running the Application
```bash
# Single check (default)
python main.py

# Continuous monitoring mode
python main.py --loop

# Verbose logging (add --verbose to any command)
python main.py --verbose
python main.py --loop --verbose
```

### Testing
```bash
# Run all unit tests (integration tests excluded by default)
pytest tests/ -v

# Run a specific test file
pytest tests/test_scraper.py -v
pytest tests/test_notifier.py -v
pytest tests/test_config.py -v

# Run integration tests (hits real qmq.app website)
pytest tests/test_integration.py -v --run-integration

# Run with specific marker
pytest tests/ -v -m "not integration"
```

## Architecture

### Core Components

The application follows a simple pipeline architecture with three main components:

1. **scraper.py** - `VisaScraper` class uses Playwright to intercept Supabase API calls from qmq.app
   - Primary method: Intercept `slot_data` API responses (`https://sdetncywjtheyqwfzshc.supabase.co/rest/v1/slot_data`)
   - Fallback method: Extract dates from page content using regex if API interception fails
   - Returns `AppointmentInfo` dataclass with city, visa_type, visa_category, and available_date

2. **notifier.py** - `EmailNotifier` class handles SMTP email notifications
   - Automatically selects SSL (port 465) for QQ/163 email or STARTTLS (port 587) for Gmail/Outlook
   - Sends bilingual (Chinese/English) HTML and plain text emails

3. **config.py** - Pydantic-settings based configuration
   - Loads from `.env` file
   - Validates date formats and SMTP settings at startup
   - Uses singleton pattern via `get_settings()` / `reset_settings()`

4. **main.py** - Entry point with asyncio event loop
   - `check_and_notify()` - single check execution
   - `run_loop()` - continuous monitoring with configurable interval

### Data Flow

```
main.py → VisaScraper.fetch_appointment() → Playwright intercepts API → Parse slot_data
                                               ↓
                    Appointment found? → EmailNotifier.send_notification()
                                               ↓
                                    SMTP (SSL or STARTTLS)
```

### Testing Strategy

- **Unit tests** (`test_*.py`): Mock external dependencies (Playwright, SMTP)
- **Integration tests** (`test_integration.py`): Require `--run-integration` flag to hit real qmq.app
- **Configuration**: `conftest.py` adds pytest options and handles test collection modification

## Configuration

Configuration is via environment variables loaded from `.env` file:

```bash
# Required
TARGET_DATE=2025-06-01          # Alert if earlier date found
SMTP_HOST=smtp.qq.com           # Or smtp.gmail.com
SMTP_PORT=465                   # 465 for SSL (QQ/163), 587 for STARTTLS (Gmail)
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_auth_code    # App password, NOT login password
NOTIFY_EMAIL=recipient@example.com

# Optional (have defaults)
CITY=北京
VISA_TYPE=F-1
VISA_CATEGORY=Other Student
CHECK_INTERVAL_MINUTES=30
QMQ_URL=https://qmq.app
```

### SMTP Provider Notes

- **Gmail**: Use port 587 with app password from https://myaccount.google.com/apppasswords
- **QQ/163**: Use port 465 with authorization code (授权码), not login password

## Key Implementation Details

### Playwright Scraping Strategy

The scraper intercepts network responses rather than parsing DOM:

```python
# In scraper.py:59-64
def handle_response(response: Response):
    if "slot_data" in response.url or self.SUPABASE_URL in response.url:
        api_responses.append(response)
```

This is more reliable than DOM parsing because qmq.app loads data via XHR/fetch.

### Date Matching Logic

The scraper filters for Beijing F-1 Other Student appointments by checking:
- `city_key` contains "cnbei", "beijing", or "北京"
- `visa_class` or `visa_type` contains "f-1"
- `visa_class` contains "other"

See `scraper.py:148-165` for the matching implementation.

### Async Patterns

The codebase uses `pytest-asyncio` with `asyncio_mode = auto` (configured in `pytest.ini`). All async tests are automatically handled without needing `@pytest.mark.asyncio` decorator in most cases.
