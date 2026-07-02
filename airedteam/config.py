from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIREDTEAM_", env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./airedteam.db"
    blob_dir: Path = Path("./blobs")
    master_key: str = Field(..., min_length=44, max_length=44)
    admin_password: str = Field(..., min_length=1)
    jwt_secret: str = "change-me-jwt"
    jwt_ttl_minutes: int = 60 * 24 * 7
    max_concurrency: int = 8
    sse_progress_hz: float = 1.0
    response_inline_max_bytes: int = 8 * 1024
    cors_origins: list[str] = ["http://localhost:5173"]
    monitor_enabled: bool = True
    dingtalk_webhook_url: str | None = None
    dingtalk_secret: str | None = None
    dingtalk_timeout_seconds: float = 5.0
    monitor_failure_rate_threshold: float = 0.2
    monitor_empty_response_rate_threshold: float = 0.1
    monitor_score_failure_rate_threshold: float = 0.2
    monitor_min_samples: int = 20
    monitor_no_progress_seconds: int = 600
    monitor_alert_cooldown_seconds: int = 900


def get_settings() -> Settings:
    return Settings()
