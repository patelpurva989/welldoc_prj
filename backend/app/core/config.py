"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "FDA Regulatory Automation Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://fda_user:fda_password@postgres:5432/fda_regulatory"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"

    # FDA APIs
    FAERS_API_URL: str = "https://api.fda.gov/drug/event.json"
    FDA_API_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS - FIXED: Allow actual frontend URLs
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3400",
        "http://localhost:3660",
        "http://frontend:3400",
        "http://frontend:3660",
        "http://72.61.11.62:3660",
        "http://72.61.11.62:3400",
        "*"  # Allow all origins for demo
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
