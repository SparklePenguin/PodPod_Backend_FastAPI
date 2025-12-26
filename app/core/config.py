import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic_settings import BaseSettings


def load_config_file(config_path: Optional[str] = None) -> dict:
    """YAML 설정 파일을 로드합니다."""
    if config_path is None:
        # 환경변수로 config 파일 지정 가능
        config_path = os.getenv("CONFIG_FILE", "config.dev.yaml")

    config_file = Path(config_path)

    if not config_file.exists():
        print(f"경고: 설정 파일 {config_path}을 찾을 수 없습니다. 기본값을 사용합니다.")
        return {}

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            print(f"설정 파일 로드 완료: {config_path}")
            return config or {}
    except Exception as e:
        print(f"설정 파일 로드 중 오류 발생: {e}")
        return {}


class Settings(BaseSettings):
    # Config 파일에서 로드할 설정
    _config: dict = {}

    # 환경 식별
    ENVIRONMENT: str = "development"

    # 데이터베이스 설정 (Config 파일에서 로드, 비밀번호는 Infisical에서)
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str  # 필수: Infisical에서 MYSQL_PASSWORD로 주입
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "podpod"

    # Redis 설정
    redis_url: str = "redis://localhost:6379/0"

    # Sendbird 설정 (Infisical에서)
    SENDBIRD_APP_ID: Optional[str] = None
    SENDBIRD_API_TOKEN: Optional[str] = None

    # JWT 설정
    secret_key: str  # Infisical에서 주입
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 앱 설정
    APP_NAME: str = "PodPod API"
    APP_VERSION: str = "1.0.0"
    ROOT_PATH: str = ""  # Nginx 프록시 경로 (예: /stg, /rm)

    # 카카오 OAuth 설정
    KAKAO_CLIENT_ID: Optional[str] = None
    KAKAO_CLIENT_SECRET: Optional[str] = None  # Infisical에서
    KAKAO_REDIRECT_URI: str = "http://localhost:3000/auth/kakao/callback"
    KAKAO_TOKEN_URL: str = "https://kauth.kakao.com/oauth/token"
    KAKAO_USER_INFO_URL: str = "https://kapi.kakao.com/v2/user/me"

    # Google OAuth 설정
    GOOGLE_CLIENT_ID: Optional[str] = None

    # Apple OAuth 설정
    APPLE_PUBLIC_KEYS_URL: str = "https://appleid.apple.com/auth/keys"
    APPLE_TOKEN_URL: str = "https://appleid.apple.com/auth/token"
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    APPLE_KEY_ID: Optional[str] = None
    APPLE_PRIVATE_KEY: Optional[str] = None
    APPLE_REDIRECT_URI: str = "http://localhost:3000/auth/apple/callback"
    APPLE_SCHEME: Optional[str] = None
    APPLE_ISSUER: str = "https://appleid.apple.com"

    # Google Sheets 설정
    GOOGLE_CREDENTIALS_PATH: str = "credentials.json"
    GOOGLE_SHEETS_ID: Optional[str] = None
    GOOGLE_SHEETS_RANGE: str = "1xxx: 인증/로그인 관련 오류!A:F"
    GOOGLE_SHEETS_CREDENTIALS: Optional[str] = None

    # Firebase Cloud Messaging 설정
    FIREBASE_SERVICE_ACCOUNT_KEY: Optional[str] = None

    # 서버 설정 (디버그 모드)
    DEBUG: bool = False

    def __init__(self, config_path: Optional[str] = None, **kwargs):
        # Config 파일 로드
        config = load_config_file(config_path)

        # Config 파일에서 값 추출하여 kwargs에 병합
        if config:
            # 환경 설정
            self._config = config
            kwargs.setdefault("ENVIRONMENT", config.get("environment", "development"))

            # 데이터베이스 설정
            db_config = config.get("database", {})
            kwargs.setdefault("MYSQL_HOST", db_config.get("host", "localhost"))
            kwargs.setdefault("MYSQL_PORT", db_config.get("port", 3306))
            kwargs.setdefault("MYSQL_DATABASE", db_config.get("name", "podpod"))
            kwargs.setdefault("MYSQL_USER", db_config.get("user", "root"))

            # JWT 설정
            jwt_config = config.get("jwt", {})
            kwargs.setdefault("ALGORITHM", jwt_config.get("algorithm", "HS256"))
            kwargs.setdefault(
                "ACCESS_TOKEN_EXPIRE_MINUTES",
                jwt_config.get("access_token_expire_minutes", 30),
            )

            # OAuth 설정
            oauth_config = config.get("oauth", {})
            kwargs.setdefault(
                "KAKAO_REDIRECT_URI",
                oauth_config.get(
                    "kakao_redirect_uri", "http://localhost:3000/auth/kakao/callback"
                ),
            )
            kwargs.setdefault(
                "APPLE_REDIRECT_URI",
                oauth_config.get(
                    "apple_redirect_uri", "http://localhost:3000/auth/apple/callback"
                ),
            )
            kwargs.setdefault(
                "KAKAO_TOKEN_URL",
                oauth_config.get(
                    "kakao_token_url", "https://kauth.kakao.com/oauth/token"
                ),
            )
            kwargs.setdefault(
                "KAKAO_USER_INFO_URL",
                oauth_config.get(
                    "kakao_user_info_url", "https://kapi.kakao.com/v2/user/me"
                ),
            )
            kwargs.setdefault(
                "APPLE_PUBLIC_KEYS_URL",
                oauth_config.get(
                    "apple_public_keys_url", "https://appleid.apple.com/auth/keys"
                ),
            )
            kwargs.setdefault(
                "APPLE_TOKEN_URL",
                oauth_config.get(
                    "apple_token_url", "https://appleid.apple.com/auth/token"
                ),
            )
            kwargs.setdefault(
                "APPLE_ISSUER",
                oauth_config.get("apple_issuer", "https://appleid.apple.com"),
            )

            # Google Sheets 설정
            sheets_config = config.get("google_sheets", {})
            kwargs.setdefault(
                "GOOGLE_CREDENTIALS_PATH",
                sheets_config.get("credentials_path", "credentials.json"),
            )
            kwargs.setdefault(
                "GOOGLE_SHEETS_RANGE",
                sheets_config.get("range", "1xxx: 인증/로그인 관련 오류!A:F"),
            )

            # 앱 설정
            app_config = config.get("app", {})
            kwargs.setdefault("APP_NAME", app_config.get("name", "PodPod API"))
            kwargs.setdefault("APP_VERSION", app_config.get("version", "1.0.0"))
            kwargs.setdefault("ROOT_PATH", app_config.get("root_path", ""))

            # 서버 설정
            server_config = config.get("server", {})
            kwargs.setdefault("DEBUG", server_config.get("debug", False))

        # 환경변수에서 민감한 정보 로드 (Infisical에서 주입)
        # MYSQL_HOST도 환경 변수로 오버라이드 가능하도록 (도커 환경 지원)
        if os.getenv("MYSQL_HOST"):
            kwargs["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
        kwargs.setdefault("MYSQL_PASSWORD", os.getenv("MYSQL_PASSWORD"))
        kwargs.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "your-secret-key-here"))
        kwargs.setdefault("SENDBIRD_APP_ID", os.getenv("SENDBIRD_APP_ID"))
        kwargs.setdefault("SENDBIRD_API_TOKEN", os.getenv("SENDBIRD_API_TOKEN"))
        kwargs.setdefault("KAKAO_CLIENT_ID", os.getenv("KAKAO_CLIENT_ID"))
        kwargs.setdefault("KAKAO_CLIENT_SECRET", os.getenv("KAKAO_CLIENT_SECRET"))
        kwargs.setdefault("GOOGLE_CLIENT_ID", os.getenv("GOOGLE_CLIENT_ID"))
        kwargs.setdefault("APPLE_CLIENT_ID", os.getenv("APPLE_CLIENT_ID"))
        kwargs.setdefault("APPLE_TEAM_ID", os.getenv("APPLE_TEAM_ID"))
        kwargs.setdefault("APPLE_KEY_ID", os.getenv("APPLE_KEY_ID"))
        kwargs.setdefault("APPLE_PRIVATE_KEY", os.getenv("APPLE_PRIVATE_KEY"))
        kwargs.setdefault("APPLE_SCHEME", os.getenv("APPLE_SCHEME"))
        kwargs.setdefault("GOOGLE_SHEETS_ID", os.getenv("GOOGLE_SHEETS_ID"))
        kwargs.setdefault(
            "GOOGLE_SHEETS_CREDENTIALS", os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        )
        kwargs.setdefault(
            "FIREBASE_SERVICE_ACCOUNT_KEY", os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        )

        super().__init__(**kwargs)

        # 필수 환경변수 검증
        if not self.MYSQL_PASSWORD:
            raise ValueError(
                "MYSQL_PASSWORD 환경변수가 설정되지 않았습니다. "
                "Infisical을 사용하여 환경변수를 주입해주세요."
            )

        print(f"환경 설정 완료: {self.ENVIRONMENT}")
        print(
            f"데이터베이스: {self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def DATABASE_URL(self) -> str:
        import urllib.parse

        encoded_password = urllib.parse.quote(self.MYSQL_PASSWORD, safe="")
        return f"mysql+aiomysql://{self.MYSQL_USER}:{encoded_password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"


# 전역 settings 인스턴스
settings = Settings()
