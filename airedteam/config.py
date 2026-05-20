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


def get_settings() -> Settings:
    return Settings()
