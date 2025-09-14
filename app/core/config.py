from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # 데이터베이스 설정 (Infisical에서 가져옴 - 필수 환경변수)
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str  # 필수: Infisical에서 MYSQL_PASSWORD로 주입되어야 함
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "podpod"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 필수 환경변수 검증
        if not self.MYSQL_PASSWORD:
            raise ValueError(
                "MYSQL_PASSWORD 환경변수가 설정되지 않았습니다. "
                "Infisical을 사용하여 환경변수를 주입해주세요. "
                "직접 환경변수 설정은 지원되지 않습니다."
            )

    @property
    def DATABASE_URL(self) -> str:
        import urllib.parse

        encoded_password = urllib.parse.quote(self.MYSQL_PASSWORD, safe="")
        return f"mysql+aiomysql://{self.MYSQL_USER}:{encoded_password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 앱 설정
    APP_NAME: str = "PodPod API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, production

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
    APPLE_TOKEN_URL: str = "https://appleid.apple.com/auth/token"
    APPLE_CLIENT_ID: Optional[str] = os.getenv("APPLE_CLIENT_ID")  # Apple App ID
    APPLE_TEAM_ID: Optional[str] = os.getenv("APPLE_TEAM_ID")  # Apple Team ID
    APPLE_KEY_ID: Optional[str] = os.getenv("APPLE_KEY_ID")  # Apple Key ID
    APPLE_PRIVATE_KEY: Optional[str] = os.getenv(
        "APPLE_PRIVATE_KEY"
    )  # Apple Private Key (PEM 형식)
    APPLE_REDIRECT_URI: str = (
        "http://localhost:3000/auth/apple/callback"  # Apple Redirect URI
    )
    APPLE_SCHEME: Optional[str] = os.getenv("APPLE_SCHEME")
    APPLE_ISSUER: str = "https://appleid.apple.com"

    # Google Sheets 설정
    GOOGLE_CREDENTIALS_PATH: str = "credentials.json"
    GOOGLE_SHEETS_ID: Optional[str] = os.getenv("GOOGLE_SHEETS_ID")
    GOOGLE_SHEETS_RANGE: str = os.getenv(
        "GOOGLE_SHEETS_RANGE", "1xxx: 인증/로그인 관련 오류!A:F"
    )
    GOOGLE_SHEETS_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_SHEETS_CREDENTIALS")


settings = Settings()
