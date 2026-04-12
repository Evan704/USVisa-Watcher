# tests/test_notifier.py
from datetime import date
from unittest.mock import Mock, patch

import pytest

from config import Settings
from notifier import EmailNotifier


class TestEmailNotifier:
    @pytest.fixture
    def mock_settings(self):
        settings = Mock(spec=Settings)
        settings.smtp_host = "smtp.test.com"
        settings.smtp_port = 587
        settings.smtp_user = "test@example.com"
        settings.smtp_password = "password"
        settings.notify_email = "alert@example.com"
        settings.city = "北京"
        settings.visa_type = "F-1"
        settings.visa_category = "Other Student"
        settings.target_date = date(2025, 6, 1)
        return settings

    @patch("notifier.smtplib.SMTP")
    def test_send_notification_success(self, mock_smtp_class, mock_settings):
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        notifier = EmailNotifier(mock_settings)
        result = notifier.send_notification(date(2025, 5, 15))

        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@example.com", "password")
        mock_smtp.send_message.assert_called_once()

    @patch("notifier.smtplib.SMTP")
    def test_send_notification_failure(self, mock_smtp_class, mock_settings):
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)
        mock_smtp.send_message.side_effect = Exception("SMTP error")

        notifier = EmailNotifier(mock_settings)
        result = notifier.send_notification(date(2025, 5, 15))

        assert result is False

    def test_build_email_content(self, mock_settings):
        notifier = EmailNotifier(mock_settings)
        msg = notifier._build_message(date(2025, 5, 15))

        assert "北京" in msg["Subject"]
        assert "F-1" in msg["Subject"]
        assert "alert@example.com" in msg["To"]
        assert "test@example.com" in msg["From"]

        # Get the text/plain payload and decode if necessary
        text_payload = msg.get_payload()[0].get_payload()
        if isinstance(text_payload, bytes):
            text_payload = text_payload.decode('utf-8')
        elif isinstance(text_payload, str) and 'base64' in str(msg.get_payload()[0].get('Content-Transfer-Encoding', '')).lower():
            import base64
            text_payload = base64.b64decode(text_payload).decode('utf-8')
        assert "2025-05-15" in text_payload
