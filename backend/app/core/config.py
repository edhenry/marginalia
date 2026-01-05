"""Application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App settings
    app_name: str = "Marginalia"
    debug: bool = False
    environment: Literal["development", "production", "test"] = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./marginalia.db"

    # Storage
    storage_path: Path = Path("./storage")
    pdf_storage_path: Path = Path("./storage/pdfs")

    # Claude API
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Notion Integration
    notion_api_key: str = ""
    notion_queue_database_id: str = ""
    notion_research_agenda_database_id: str = ""

    # Obsidian Integration
    obsidian_vault_path: str = ""
    obsidian_inbox_folder: str = "inbox"
    obsidian_concepts_folder: str = "concepts"

    # Security
    secret_key: str = "development-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    # API
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
