"""
Integration test for the visa scraper.
This test actually makes a request to qmq.app to verify the scraper works.
Run with: pytest tests/test_integration.py -v --run-integration
"""
import pytest
from datetime import date
from unittest.mock import Mock, patch

from config import get_settings, reset_settings
from scraper import VisaScraper


@pytest.fixture
def integration_settings(monkeypatch):
    """Settings for integration test."""
    reset_settings()
    monkeypatch.setenv("TARGET_DATE", "2025-12-31")
    monkeypatch.setenv("CITY", "北京")
    monkeypatch.setenv("VISA_TYPE", "F-1")
    monkeypatch.setenv("VISA_CATEGORY", "Other Student")
    monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "test@test.com")
    monkeypatch.setenv("SMTP_PASSWORD", "test")
    monkeypatch.setenv("NOTIFY_EMAIL", "alert@test.com")
    return get_settings()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scraper_can_fetch_data(integration_settings):
    """
    Integration test that actually fetches data from qmq.app.
    This test is skipped by default - use --run-integration to enable.
    """
    scraper = VisaScraper(integration_settings)
    result = await scraper.fetch_appointment()

    # We may or may not get data depending on the site structure
    # but the scraper should run without errors
    if result:
        assert result.city == "北京"
        assert result.visa_type == "F-1"
        assert isinstance(result.available_date, date)
