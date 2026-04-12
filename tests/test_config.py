# tests/test_config.py
import os
import pytest
from pydantic import ValidationError

from config import Settings


class TestSettings:
    def test_valid_settings(self, monkeypatch):
        monkeypatch.setenv("TARGET_DATE", "2025-12-31")
        monkeypatch.setenv("CITY", "北京")
        monkeypatch.setenv("VISA_TYPE", "F-1")
        monkeypatch.setenv("VISA_CATEGORY", "Other Student")
        monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "test@gmail.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("NOTIFY_EMAIL", "alert@gmail.com")

        settings = Settings()
        assert settings.target_date.isoformat() == "2025-12-31"
        assert settings.city == "北京"
        assert settings.visa_type == "F-1"
        assert settings.visa_category == "Other Student"
        assert settings.smtp_host == "smtp.gmail.com"
        assert settings.smtp_port == 587

    def test_invalid_date_format(self, monkeypatch):
        monkeypatch.setenv("TARGET_DATE", "invalid-date")
        with pytest.raises(ValidationError):
            Settings()

    def test_missing_required_field(self, monkeypatch):
        monkeypatch.setenv("TARGET_DATE", "2025-12-31")
        with pytest.raises(ValidationError):
            Settings()
