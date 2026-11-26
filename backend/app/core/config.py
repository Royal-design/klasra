from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "School LMS API"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_v1_prefix: str = "/api/v1"

    # Required: no hardcoded database credentials or default fallback.
    # TODO(security): Enforce TLS/mTLS (sslmode=verify-full) for non-local database
    # connections before staging/production deployment.
    database_url: str

    # Comma-separated or JSON list of trusted frontend origins. Never allow "*".
    cors_origins: str = "http://localhost:3000"

    # Session & cookie hardening
    session_ttl_hours: int = 12
    cookie_secure: bool = True

    # Rate limiting (per IP per minute)
    # TODO(security): Replace in-memory rate limiter with Redis-backed store for multi-instance production.
    rate_limit_per_minute: int = 120
    login_rate_limit_per_minute: int = 15

    # Transactional email provider (Resend in staging/production; console in dev/test)
    email_provider: Literal["console", "resend"] = "console"
    resend_api_key: str | None = None
    email_from: str | None = None
    frontend_base_url: str = "http://localhost:3000"

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must specify at least one trusted origin.")
        if "*" in origins:
            raise ValueError("Wildcard '*' is not permitted in CORS_ORIGINS.")
        return ",".join(origins)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def session_cookie_name(self) -> str:
        return "__Host-lms_session" if self.cookie_secure else "lms_session"

    @property
    def csrf_cookie_name(self) -> str:
        return "__Host-lms_csrf" if self.cookie_secure else "lms_csrf"


@lru_cache
def get_settings() -> Settings:
    # BaseSettings loads required fields like DATABASE_URL from env/.env at runtime.
    return Settings()  # pyright: ignore[reportCallIssue]
