# tests/test_main.py
from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pytest

from main import check_and_notify, main


class TestCheckAndNotify:
    @patch("main.VisaScraper")
    @patch("main.EmailNotifier")
    @patch("main.get_settings")
    @pytest.mark.asyncio
    async def test_check_finds_earlier_date(self, mock_get_settings, mock_notifier_class, mock_scraper_class):
        # Setup mocks
        mock_settings = Mock()
        mock_settings.target_date = date(2025, 6, 1)
        mock_get_settings.return_value = mock_settings

        mock_scraper = Mock()
        mock_appointment = Mock()
        mock_appointment.available_date = date(2025, 5, 15)
        mock_appointment.is_earlier_than.return_value = True
        mock_scraper.fetch_appointment = AsyncMock(return_value=mock_appointment)
        mock_scraper_class.return_value = mock_scraper

        mock_notifier = Mock()
        mock_notifier.send_notification.return_value = True
        mock_notifier_class.return_value = mock_notifier

        result = await check_and_notify()

        assert result is True
        mock_notifier.send_notification.assert_called_once_with(date(2025, 5, 15))

    @patch("main.VisaScraper")
    @patch("main.EmailNotifier")
    @patch("main.get_settings")
    @pytest.mark.asyncio
    async def test_check_finds_later_date(self, mock_get_settings, mock_notifier_class, mock_scraper_class):
        mock_settings = Mock()
        mock_settings.target_date = date(2025, 6, 1)
        mock_get_settings.return_value = mock_settings

        mock_scraper = Mock()
        mock_appointment = Mock()
        mock_appointment.available_date = date(2025, 7, 15)
        mock_appointment.is_earlier_than.return_value = False
        mock_scraper.fetch_appointment = AsyncMock(return_value=mock_appointment)
        mock_scraper_class.return_value = mock_scraper

        mock_notifier = Mock()
        mock_notifier_class.return_value = mock_notifier

        result = await check_and_notify()

        assert result is False
        mock_notifier.send_notification.assert_not_called()

    @patch("main.VisaScraper")
    @patch("main.get_settings")
    @pytest.mark.asyncio
    async def test_check_no_data(self, mock_get_settings, mock_scraper_class):
        mock_settings = Mock()
        mock_settings.target_date = date(2025, 6, 1)
        mock_get_settings.return_value = mock_settings

        mock_scraper = Mock()
        mock_scraper.fetch_appointment = AsyncMock(return_value=None)
        mock_scraper_class.return_value = mock_scraper

        result = await check_and_notify()

        assert result is False
