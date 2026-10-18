"""Environment-backed settings for the Document AI integration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    google_cloud_project: str = ""
    documentai_location: str = ""
    documentai_processor_id: str = ""
    documentai_processor_version_id: str | None = None
    documentai_field_mask: str | None = None
    max_upload_size_bytes: int = 20 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
