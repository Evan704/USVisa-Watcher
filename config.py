# config.py
from datetime import date
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Scraping settings
    target_date: date = Field(description="Threshold date - alert if earlier date found")
    city: str = Field(default="北京", description="City for visa appointment")
    visa_type: str = Field(default="F-1", description="Visa type")
    visa_category: str = Field(default="Other Student", description="Visa category")
    qmq_url: str = Field(
        default="https://qmq.app",
        description="Base URL for qmq.app"
    )

    # SMTP settings
    smtp_host: str = Field(description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: str = Field(description="SMTP username/email")
    smtp_password: str = Field(description="SMTP password or app-specific password")

    # Notification settings
    notify_email: str = Field(description="Email to send alerts to")
    check_interval_minutes: int = Field(
        default=30,
        description="Minutes between checks when running in loop mode"
    )

    @field_validator("target_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        raise ValueError(f"Invalid date format: {v}")

    @field_validator("smtp_port", mode="before")
    @classmethod
    def parse_port(cls, v):
        if isinstance(v, int):
            return v
        return int(v)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    global _settings
    _settings = None
