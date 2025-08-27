from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite+aiosqlite:///./podpod.db"

    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 앱 설정
    APP_NAME: str = "PodPod API"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"


settings = Settings()
