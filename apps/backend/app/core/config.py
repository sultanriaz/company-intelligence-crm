from typing import List, Optional
import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    APP_NAME: str = "Company Intelligence & Outreach Platform"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Security & Auth
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-min-32-chars-long"
    ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./crm_intelligence.db"
    SYNC_DATABASE_URL: str = "sqlite:///./crm_intelligence.db"
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Scraper & SSRF Settings
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (compatible; CompanyIntelligenceBot/1.0; +https://company-intelligence.local/bot)"
    SCRAPER_TIMEOUT_SECONDS: int = 20
    SCRAPER_MAX_PAGES_PER_DOMAIN: int = 50
    SCRAPER_MAX_CONCURRENT_REQUESTS: int = 3
    SCRAPER_REQUEST_DELAY_SECONDS: float = 0.5
    PLAYWRIGHT_ENABLED: bool = False

    # Agent Limits
    AGENT_MAX_RETRIES: int = 3
    AGENT_MAX_EXECUTION_SECONDS: int = 300
    AGENT_MAX_COST_USD_PER_RUN: float = 2.00

    # AI / LLM Providers
    LLM_PROVIDER: str = "ollama"  # ollama, openai, mock
    LLM_MODEL: str = "mistral:latest"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral:latest"
    OLLAMA_TIMEOUT_SECONDS: float = 180.0
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Search Provider
    SEARCH_PROVIDER: str = "mock"  # mock, serpapi, tavily
    SEARCH_API_KEY: Optional[str] = None

    # Email Settings
    EMAIL_PROVIDER: str = "mock"  # mock, resend, sendgrid, ses
    RESEND_API_KEY: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    EMAIL_FROM_ADDRESS: str = "outreach@company-intelligence.local"
    EMAIL_FROM_NAME: str = "Company Intelligence Team"
    EMAIL_REPLY_TO: str = "replies@company-intelligence.local"
    EMAIL_WEBHOOK_SECRET: str = "dev-webhook-secret-signing-key"

    EMAIL_DRY_RUN: bool = True
    EMAIL_REQUIRE_APPROVAL: bool = True
    EMAIL_AUTO_SEND_ENABLED: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
