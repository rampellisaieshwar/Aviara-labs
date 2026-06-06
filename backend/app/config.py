import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    
    # Database URL configuration (Supports Async PostgreSQL connection by default)
    # e.g., postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leads_db"
    
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
