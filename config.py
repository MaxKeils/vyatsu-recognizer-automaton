from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class _Settings(BaseSettings):
    """Настройки приложения."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # Сервер
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS
    cors_origins: List[str] = ["http://localhost:8080"]
    
    # API
    api_prefix: str = "/api/v1"
    
    # База данных (PostgreSQL)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/automaton"

_settings_instance = None

def get_settings() -> _Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = _Settings()
    return _settings_instance
