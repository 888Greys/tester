from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = ConfigDict(
        extra='ignore', 
        protected_namespaces=(),
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
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
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # Django Integration
    django_base_url: Optional[str] = None
    django_api_token: Optional[str] = None
    
    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "gukas_memory"
    postgres_user: str = "gukas_user"
    postgres_password: str = "gukas_password"
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "memory_vectors"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Vector Memory Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    max_memory_items: int = 1000
    memory_retention_days: int = 365
    similarity_threshold: float = 0.7

def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()
