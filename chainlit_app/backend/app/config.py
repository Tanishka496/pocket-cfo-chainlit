"""
Application configuration settings.

Centralized configuration for the FastAPI application.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # JWT
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    
    # API
    API_TITLE: str = "AI Pocket CFO - Transaction Management"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Full-featured transaction management module for small business"
    
    # CORS
    ALLOWED_ORIGINS: list = ["*"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()
