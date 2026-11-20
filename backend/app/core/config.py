from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _use_psycopg_driver(url: str) -> str:
    """Hosts hand out URLs like postgres://... ; SQLAlchemy needs postgresql+psycopg://..."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


class Settings(BaseSettings):
    """App settings. Every value comes from an environment variable (or a local .env file).

    Pydantic validates them at startup, so a missing secret fails fast instead of at request time.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str
    test_database_url: str | None = None

    # Auth
    jwt_secret: str = Field(min_length=32)
    jwt_expire_hours: int = 24
    auth_cookie_name: str = "access_token"

    # Runtime
    environment: Literal["development", "test", "production"] = "development"
    frontend_origin: str = "http://localhost:5173"
    app_url: str = "http://localhost:5173"
    currency: str = "INR"
    app_timezone: str = "Asia/Kolkata"
    # Production only: folder holding the built React app, served by FastAPI.
    static_dir: str | None = None
    # Header that holds the visitor's real IP, set by the host's proxy (used for rate
    # limits). Render sits behind Cloudflare, which sets True-Client-IP and overwrites any
    # value the visitor sends. Never use X-Forwarded-For here: on Render a visitor can
    # put any IP at its start. Unset (local dev) = the address of the direct connection.
    client_ip_header: str | None = None

    # Reminders / email
    cron_secret: str | None = None
    email_provider: Literal["console", "smtp", "brevo"] = "console"
    email_from_name: str = "Personal Tracker"
    email_from_address: str = "reminders@tracker.local"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = True
    brevo_api_key: str | None = None

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _normalise_db_url(cls, value: str | None) -> str | None:
        return _use_psycopg_driver(value) if value else value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # required fields are read from the environment
