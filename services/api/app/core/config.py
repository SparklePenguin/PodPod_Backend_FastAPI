import enum
import json
import os
import urllib.parse
from pathlib import Path
from typing import Optional

import yaml
from pydantic_settings import BaseSettings


def load_config_file(config_path: str | None = None) -> dict:
    """YAML 설정 파일을 로드합니다."""
    if config_path is None:
        # 환경변수로 config 파일 지정 가능
        config_path = os.getenv("CONFIG_FILE", "")

    config_file = Path(config_path)

    # 절대 경로가 아니고 파일이 존재하지 않으면, 프로젝트 루트에서 찾기 시도
    if not config_file.is_absolute() and not config_file.exists():
        # 프로젝트 루트 찾기 (services/api/app/core/config.py에서 5단계 위)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent.parent
        config_file = project_root / config_path

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


class Profile(enum.Enum):
    local = "local"
    DEV = "development"
    STG = "staging"
    PRD = "production"

    @classmethod
    def convert(cls, value):
        for e in cls:
            if value == e.value:
                return e
        raise Exception("허용되지 않는 Profile")


class AppConfig(BaseSettings):
    profile: str
    name: str
    description: str
    version: str
    base_url: str
    root_path: str
    host: str
    port: int
    reload: bool
    debug: bool


class DataBaseConfig(BaseSettings):
    host: str
    port: int
    name: str
    user: str
    password: str = os.getenv("MYSQL_PASSWORD")

    def get_url(self):
        encoded_password = urllib.parse.quote(self.password, safe="")
        return f"mysql+aiomysql://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.name}"


class JwtConfig(BaseSettings):
    secret_key: str = os.getenv("SECRET_KEY")  # Infisical에서 주입
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class RedisConfig(BaseSettings):
    host: str
    port: int
    db: int

    def get_url(self):
        return f"redis://{self.host}:{self.port}/{self.db}"


class LoggingConfig(BaseSettings):
    level: str
    console: bool
    file_rotation: bool
    retention_days: int  # 개발 환경에서는 짧게 보관
    max_file_size: str


class ChatConfig(BaseSettings):
    use_websocket: bool


class InfisicalConfig(BaseSettings):
    enabled: bool
    env: str


class Settings(BaseSettings):
    # Config 파일에서 로드할 설정
    _config: dict = {}

    # 환경 식별
    ENVIRONMENT: str = "development"
    database: DataBaseConfig | None = None  # MySQL 데이터베이스 설정
    redis: RedisConfig | None = None  # MARK: - Redis
    jwt: JwtConfig | None = None  # MARK: - JWT
    app: AppConfig | None = None  # MARK: - App, Server
    logging: LoggingConfig | None = None
    chat: ChatConfig | None = None
    infisical: InfisicalConfig | None = None

    DEBUG: bool = False

    # MARK: - File Storage

    UPLOADS_DIR: str | None = None  # 환경별로 다르게 설정됨
    LOGS_DIR: str | None = None  # 환경별로 다르게 설정됨

    # MARK: - OAuth (Infisical)
    # Note: REDIRECT_URI는 base_url을 사용해 자동 생성됩니다 (@property 참고)

    # 카카오 OAuth
    KAKAO_CLIENT_ID: str | None = os.getenv("KAKAO_CLIENT_ID")
    KAKAO_CLIENT_SECRET: str | None = os.getenv("KAKAO_CLIENT_SECRET")

    # 네이버 OAuth
    NAVER_CLIENT_ID: str | None = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET: str | None = os.getenv("NAVER_CLIENT_SECRET")

    # 구글 OAuth
    GOOGLE_CLIENT_ID: str | None = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = os.getenv("GOOGLE_CLIENT_SECRET")

    # 애플 OAuth
    APPLE_CLIENT_ID: str | None = os.getenv("APPLE_CLIENT_ID")
    APPLE_TEAM_ID: str | None = os.getenv("APPLE_TEAM_ID")
    APPLE_KEY_ID: str | None = os.getenv("APPLE_KEY_ID")
    APPLE_PRIVATE_KEY: str | None = os.getenv("APPLE_PRIVATE_KEY")
    APPLE_SCHEME: str | None = os.getenv("APPLE_SCHEME")

    # 안드로이드 패키지명
    ANDROID_PACKAGE_NAME: Optional[str] = os.getenv("ANDROID_PACKAGE_NAME")

    # Firebase Cloud Messaging
    FIREBASE_SERVICE_ACCOUNT_KEY: str | None = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")

    # MARK: - Chat Service
    USE_WEBSOCKET_CHAT: bool | None = os.getenv("USE_WEBSOCKET_CHAT", False)  # True면 WebSocket 사용, False면 Sendbird 사용

    @classmethod
    def load(cls):
        return cls(**load_config_file())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ENVIRONMENT = os.getenv("PROFILE")
        self.set_dirs()

        print(f"환경 설정 완료: {self.ENVIRONMENT}")
        print(
            f"Config: {json.dumps(self.model_dump(), indent=4, ensure_ascii=False)}"
        )
        print(f"Base URL: {self.app.base_url}")
        print(f"Uploads 디렉토리: {self.UPLOADS_DIR}")
        print(f"Logs 디렉토리: {self.LOGS_DIR}")

    def set_dirs(self):
        profile = Profile.convert(self.ENVIRONMENT)

        self.UPLOADS_DIR = f"/Users/Shared/Projects/PodPod/uploads/{profile.value}"
        self.LOGS_DIR = f"/Users/Shared/Projects/PodPod/logs/{profile.value}"

        # uploads 디렉토리가 없으면 생성
        Path(self.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

        # logs 디렉토리가 없으면 생성
        Path(self.LOGS_DIR).mkdir(parents=True, exist_ok=True)

    @property
    def DATABASE_URL(self) -> str:
        """데이터베이스 URL을 생성합니다."""
        return self.database.get_url()

    # MARK: - OAuth Redirect URIs (자동 생성)

    @property
    def KAKAO_REDIRECT_URI(self) -> str:
        """카카오 OAuth 리다이렉트 URI를 base_url로부터 생성합니다."""
        return f"{self.app.base_url}/api/v1/oauth/kakao/callback"

    @property
    def NAVER_REDIRECT_URI(self) -> str:
        """네이버 OAuth 리다이렉트 URI를 base_url로부터 생성합니다."""
        return f"{self.app.base_url}/api/v1/oauth/naver/callback"

    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        """구글 OAuth 리다이렉트 URI를 base_url로부터 생성합니다."""
        return f"{self.app.base_url}/api/v1/oauth/google/callback"

    @property
    def APPLE_REDIRECT_URI(self) -> str:
        """애플 OAuth 리다이렉트 URI를 base_url로부터 생성합니다."""
        return f"{self.app.base_url}/api/v1/oauth/apple/callback"

    # MARK: - OAuth URLs (상수)

    @property
    def KAKAO_TOKEN_URL(self) -> str:
        return "https://kauth.kakao.com/oauth/token"

    @property
    def KAKAO_USER_INFO_URL(self) -> str:
        return "https://kapi.kakao.com/v2/user/me"

    @property
    def APPLE_PUBLIC_KEYS_URL(self) -> str:
        return "https://appleid.apple.com/auth/keys"

    @property
    def APPLE_TOKEN_URL(self) -> str:
        return "https://appleid.apple.com/auth/token"

    @property
    def APPLE_ISSUER(self) -> str:
        return "https://appleid.apple.com"


# 전역 settings 인스턴스
settings = Settings.load()
