from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIREDTEAM_", env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./airedteam.db"
    blob_dir: Path = Path("./blobs")
    master_key: str = Field(..., min_length=44, max_length=44)
    admin_password: str = Field(..., min_length=1)
    jwt_secret: str = "change-me-jwt"
    jwt_ttl_minutes: int = 60 * 24 * 7
    oidc_endpoint: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: SecretStr | None = None
    oidc_callback_url: str | None = None
    frontend_url: str | None = None
    oidc_force_auth: bool = False
    max_concurrency: int = 8
    sse_progress_hz: float = 1.0
    response_inline_max_bytes: int = 8 * 1024
    cors_origins: list[str] = ["http://localhost:5173"]
    monitor_enabled: bool = True
    dingtalk_webhook_url: str | None = None
    dingtalk_secret: str | None = None
    dingtalk_timeout_seconds: float = 5.0
    monitor_failure_rate_threshold: float = 0.5
    monitor_empty_response_rate_threshold: float = 0.1
    monitor_score_failure_rate_threshold: float = 0.2
    monitor_min_samples: int = 20
    monitor_rate_window_seconds: int = 300
    monitor_no_progress_seconds: int = 600
    monitor_alert_cooldown_seconds: int = 900

    @field_validator(
        "oidc_endpoint",
        "oidc_client_id",
        "oidc_client_secret",
        "oidc_callback_url",
        "frontend_url",
        mode="before",
    )
    @classmethod
    def empty_oidc_values_are_unset(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def validate_oidc_configuration(self):
        fields = {
            "AIREDTEAM_OIDC_ENDPOINT": self.oidc_endpoint,
            "AIREDTEAM_OIDC_CLIENT_ID": self.oidc_client_id,
            "AIREDTEAM_OIDC_CLIENT_SECRET": self.oidc_client_secret,
            "AIREDTEAM_OIDC_CALLBACK_URL": self.oidc_callback_url,
            "AIREDTEAM_FRONTEND_URL": self.frontend_url,
        }
        configured = [name for name, value in fields.items() if value is not None]
        if configured and len(configured) != len(fields):
            missing = ", ".join(name for name, value in fields.items() if value is None)
            raise ValueError(f"partial OIDC configuration; missing: {missing}")
        if self.oidc_force_auth and not configured:
            raise ValueError("AIREDTEAM_OIDC_FORCE_AUTH requires complete OIDC configuration")
        for name, value in (
            ("AIREDTEAM_OIDC_ENDPOINT", self.oidc_endpoint),
            ("AIREDTEAM_OIDC_CALLBACK_URL", self.oidc_callback_url),
            ("AIREDTEAM_FRONTEND_URL", self.frontend_url),
        ):
            if value is not None:
                parsed = urlsplit(value)
                if (
                    parsed.scheme not in ("http", "https")
                    or not parsed.netloc
                    or parsed.username
                    or parsed.password
                ):
                    raise ValueError(f"{name} must be an http(s) URL without embedded credentials")
                if parsed.query or parsed.fragment:
                    raise ValueError(f"{name} must not contain a query string or fragment")
        return self

    @property
    def oidc_enabled(self) -> bool:
        return self.oidc_endpoint is not None


def get_settings() -> Settings:
    return Settings()
