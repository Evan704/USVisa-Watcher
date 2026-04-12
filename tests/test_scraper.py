# tests/test_scraper.py
from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pytest

from config import Settings
from scraper import AppointmentInfo, VisaScraper


class TestAppointmentInfo:
    def test_appointment_info_creation(self):
        info = AppointmentInfo(
            city="北京",
            visa_type="F-1",
            visa_category="Other Student",
            available_date=date(2025, 5, 15),
        )
        assert info.city == "北京"
        assert info.available_date == date(2025, 5, 15)

    def test_is_earlier_than_true(self):
        info = AppointmentInfo(
            city="北京",
            visa_type="F-1",
            visa_category="Other Student",
            available_date=date(2025, 5, 15),
        )
        assert info.is_earlier_than(date(2025, 6, 1)) is True

    def test_is_earlier_than_false(self):
        info = AppointmentInfo(
            city="北京",
            visa_type="F-1",
            visa_category="Other Student",
            available_date=date(2025, 7, 15),
        )
        assert info.is_earlier_than(date(2025, 6, 1)) is False

    def test_is_earlier_than_same_date(self):
        info = AppointmentInfo(
            city="北京",
            visa_type="F-1",
            visa_category="Other Student",
            available_date=date(2025, 6, 1),
        )
        assert info.is_earlier_than(date(2025, 6, 1)) is False


class TestVisaScraper:
    @pytest.fixture
    def mock_settings(self):
        settings = Mock(spec=Settings)
        settings.qmq_url = "https://qmq.app"
        settings.city = "北京"
        settings.visa_type = "F-1"
        settings.visa_category = "Other Student"
        return settings

    @pytest.mark.asyncio
    async def test_scraper_initialization(self, mock_settings):
        scraper = VisaScraper(mock_settings)
        assert scraper.settings == mock_settings
