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

    # 카카오 OAuth 설정
    KAKAO_CLIENT_ID: Optional[str] = os.getenv("KAKAO_CLIENT_ID")
    KAKAO_CLIENT_SECRET: Optional[str] = os.getenv("KAKAO_CLIENT_SECRET")
    KAKAO_REDIRECT_URI: str = "http://localhost:3000/auth/kakao/callback"
    KAKAO_TOKEN_URL: str = "https://kauth.kakao.com/oauth/token"
    KAKAO_USER_INFO_URL: str = "https://kapi.kakao.com/v2/user/me"

    # Google OAuth 설정
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")

    # Apple OAuth 설정
    APPLE_PUBLIC_KEYS_URL: str = "https://appleid.apple.com/auth/keys"
    APPLE_CLIENT_ID: Optional[str] = os.getenv("APPLE_CLIENT_ID")  # Apple App ID
    APPLE_TEAM_ID: Optional[str] = os.getenv("APPLE_TEAM_ID")  # Apple Team ID
    APPLE_KEY_ID: Optional[str] = os.getenv("APPLE_KEY_ID")  # Apple Key ID
    APPLE_PRIVATE_KEY: Optional[str] = os.getenv(
        "APPLE_PRIVATE_KEY"
    )  # Apple Private Key (PEM 형식)
    APPLE_REDIRECT_URI: str = (
        "http://localhost:3000/auth/apple/callback"  # Apple Redirect URI
    )
    APPLE_ISSUER: str = "https://appleid.apple.com"


settings = Settings()
