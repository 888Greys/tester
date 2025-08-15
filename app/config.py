"""
Application configuration management.
Handles environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Info
    app_name: str = "Gukas AI Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8001
    
    # Cerebras API Configuration
    cerebras_api_key: str
    cerebras_base_url: str = "https://api.cerebras.ai/v1"
    cerebras_model: str = "gpt-oss-120b"
    
    # Django Backend Integration
    django_base_url: str
    django_api_token: Optional[str] = None
    
    # Service Authentication
    service_secret_key: str = "gukas-ai-agent-service-secret-2024-production-key"
    
    # Request Configuration
    max_tokens: int = 1000
    temperature: float = 0.7
    request_timeout: int = 30
    
    # Database Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "gukas_memory"
    postgres_user: str = "gukas_user"
    postgres_password: str = "gukas_password"
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()