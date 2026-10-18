"""Environment-backed settings for the Document AI integration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    google_cloud_project: str = ""
    invoice_documentai_location: str = ""
    invoice_documentai_processor_id: str = ""
    invoice_documentai_processor_version_id: str | None = None
    invoice_documentai_field_mask: str | None = None
    po_documentai_location: str = ""
    po_documentai_processor_id: str = ""
    po_documentai_processor_version_id: str | None = None
    po_documentai_field_mask: str | None = None
    root_agent_url: str = ""
    max_upload_size_bytes: int = 20 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
