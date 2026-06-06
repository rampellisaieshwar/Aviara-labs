import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    
    # Database URL configuration (Supports Async PostgreSQL connection by default)
    # e.g., postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leads_db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def convert_postgresql_scheme(cls, value: str) -> str:
        if value:
            # Standardize postgres:// to postgresql://
            if value.startswith("postgres://"):
                value = value.replace("postgres://", "postgresql://", 1)
            # Inject asyncpg driver for async SQLAlchemy
            if value.startswith("postgresql://") and "+asyncpg" not in value:
                value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value
    
    # Optional Sync Database URL for scripts/migrations if needed
    SYNC_DATABASE_URL: Optional[str] = "postgresql://postgres:postgres@localhost:5432/leads_db"

    # Groq LLM API Settings
    GROQ_API_KEY: str = "gsk_mock_api_key_for_testing"
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # Optional API Key Authentication
    API_KEY: Optional[str] = None

    # Load configuration from a .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
