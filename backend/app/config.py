"""
Application configuration loaded from environment variables / .env file.
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://cascadeiq:cascadeiq@localhost:5432/cascadeiq"
    database_url_sync: str = "postgresql://cascadeiq:cascadeiq@localhost:5432/cascadeiq"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    # Single authority user; credentials must be provided through the environment.
    authority_username: str = "authority"
    authority_password: str = Field(min_length=1)

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

    # Data paths
    data_dir: str = "data"
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"

    # Replay settings
    replay_speed_multiplier: float = 3600.0  # 1 real second = 1 simulation hour


settings = Settings()
