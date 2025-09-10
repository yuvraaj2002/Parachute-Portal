from pydantic_settings import BaseSettings
from typing import List
import random
from rich import print

class Settings(BaseSettings):
    """Application settings"""
    
    # API settings
    api_title: str = "Parachute Portal API"
    api_description: str = "A FastAPI application for Parachute Portal"
    api_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # JWT Settings
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # OpenAI settings
    openai_api_key: str = ""

    # PostgreSQL settings
    postgresql_db: str = ""

    # Mistral API key
    mistral_api_key: str = ""

    # AWS credentials
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = ""
    aws_bucket_name:str = ""

    # Optional Fernet encryption key (urlsafe base64-encoded 32-byte key). If set, used for file encryption/decryption across hosts
    encryption_key: str = ""
    
    # Redis settings for Celery
    redis_url: str = "redis://localhost:6379/0"
    
    # Redis connection pool settings
    redis_max_connections: int = 20
    redis_socket_connect_timeout: int = 5
    redis_socket_timeout: int = 5
    redis_health_check_interval: int = 30
    redis_retry_on_timeout: bool = True
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Create settings instance
settings = Settings()


if __name__ == "__main__":
    for i in range(10):
        print(settings.get_random_voice())