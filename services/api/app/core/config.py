import os
import urllib.parse
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings


def load_config_file(config_path: str | None = None) -> dict:
    """YAML 설정 파일을 로드합니다."""
    if config_path is None:
        # 환경변수로 config 파일 지정 가능
        config_path = os.getenv("CONFIG_FILE", "config.dev.yaml")

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


class Settings(BaseSettings):
    # Config 파일에서 로드할 설정
    _config: dict = {}

    # MARK: - Environment

    # 환경 식별
    ENVIRONMENT: str = "development"

    # MARK: - Database

    # MySQL 데이터베이스 설정
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str  # 필수: Infisical에서 주입
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "podpod"

    # MARK: - Redis

    redis_url: str = "redis://localhost:6379/0"

    # MARK: - JWT

    secret_key: str  # Infisical에서 주입
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # MARK: - App

    APP_NAME: str = "PodPod API"
    APP_VERSION: str = "1.0.0"
    ROOT_PATH: str = ""  # Nginx 프록시 경로 (예: /stg, /prod)
    base_url: str = "http://localhost:8000"  # OAuth 리다이렉트 URL 생성에 사용

    # MARK: - Server

    DEBUG: bool = False

    # MARK: - File Storage

    UPLOADS_DIR: str | None = None  # 환경별로 다르게 설정됨
    LOGS_DIR: str | None = None  # 환경별로 다르게 설정됨

    # MARK: - Chat Service

    USE_WEBSOCKET_CHAT: bool = False  # True면 WebSocket 사용, False면 Sendbird 사용
    SENDBIRD_APP_ID: str | None = None
    SENDBIRD_API_TOKEN: str | None = None

    # MARK: - OAuth (Infisical)
    # Note: REDIRECT_URI는 base_url을 사용해 자동 생성됩니다 (@property 참고)

    # 카카오 OAuth
    KAKAO_CLIENT_ID: str | None = None
    KAKAO_CLIENT_SECRET: str | None = None

    # 네이버 OAuth
    NAVER_CLIENT_ID: str | None = None
    NAVER_CLIENT_SECRET: str | None = None

    # 구글 OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # 애플 OAuth
    APPLE_CLIENT_ID: str | None = None
    APPLE_TEAM_ID: str | None = None
    APPLE_KEY_ID: str | None = None
    APPLE_PRIVATE_KEY: str | None = None
    APPLE_SCHEME: str | None = None

    # MARK: - External Services (Infisical)

    # Firebase Cloud Messaging
    FIREBASE_SERVICE_ACCOUNT_KEY: str | None = None

    # Google Sheets
    GOOGLE_SHEETS_ID: str | None = None
    GOOGLE_SHEETS_CREDENTIALS: str | None = None
    GOOGLE_CREDENTIALS_PATH: str = "credentials.json"
    GOOGLE_SHEETS_RANGE: str = "1xxx: 인증/로그인 관련 오류!A:F"

    def __init__(self, config_path: str | None = None, **kwargs):
        # Config 파일 로드
        config = load_config_file(config_path)

        # Config 파일에서 값 추출하여 kwargs에 병합
        if config:
            self._config = config
            kwargs.setdefault("ENVIRONMENT", config.get("environment", "development"))

            # 데이터베이스 설정
            db_config = config.get("database", {})
            kwargs.setdefault("MYSQL_HOST", db_config.get("host", "localhost"))
            kwargs.setdefault("MYSQL_PORT", db_config.get("port", 3306))
            kwargs.setdefault("MYSQL_DATABASE", db_config.get("name", "podpod"))
            kwargs.setdefault("MYSQL_USER", db_config.get("user", "root"))

            # Redis 설정
            redis_config = config.get("redis", {})
            kwargs.setdefault(
                "redis_url", redis_config.get("url", "redis://localhost:6379/0")
            )

            # JWT 설정
            jwt_config = config.get("jwt", {})
            kwargs.setdefault("ALGORITHM", jwt_config.get("algorithm", "HS256"))
            kwargs.setdefault(
                "ACCESS_TOKEN_EXPIRE_MINUTES",
                jwt_config.get("access_token_expire_minutes", 30),
            )

            # 앱 설정
            app_config = config.get("app", {})
            kwargs.setdefault("APP_NAME", app_config.get("name", "PodPod API"))
            kwargs.setdefault("APP_VERSION", app_config.get("version", "1.0.0"))
            kwargs.setdefault("ROOT_PATH", app_config.get("root_path", ""))
            kwargs.setdefault(
                "base_url", app_config.get("base_url", "http://localhost:8000")
            )

            # 서버 설정
            server_config = config.get("server", {})
            kwargs.setdefault("DEBUG", server_config.get("debug", False))

            # 채팅 서비스 설정
            chat_config = config.get("chat", {})
            kwargs.setdefault(
                "USE_WEBSOCKET_CHAT", chat_config.get("use_websocket", False)
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

        # 환경변수에서 민감한 정보 로드 (환경변수가 우선순위)
        # USE_WEBSOCKET_CHAT도 환경변수로 오버라이드 가능
        use_websocket_env = os.getenv("USE_WEBSOCKET_CHAT")
        if use_websocket_env:
            kwargs["USE_WEBSOCKET_CHAT"] = use_websocket_env.lower() == "true"

        # MYSQL_HOST도 환경 변수로 오버라이드 가능하도록 (도커 환경 지원)
        if os.getenv("MYSQL_HOST"):
            kwargs["MYSQL_HOST"] = os.getenv("MYSQL_HOST")

        # base_url 환경변수 override
        if os.getenv("BASE_URL"):
            kwargs["base_url"] = os.getenv("BASE_URL")

        # 데이터베이스
        kwargs.setdefault("MYSQL_PASSWORD", os.getenv("MYSQL_PASSWORD"))

        # JWT
        kwargs.setdefault("secret_key", os.getenv("SECRET_KEY", "your-secret-key-here"))

        # Sendbird
        kwargs.setdefault("SENDBIRD_APP_ID", os.getenv("SENDBIRD_APP_ID"))
        kwargs.setdefault("SENDBIRD_API_TOKEN", os.getenv("SENDBIRD_API_TOKEN"))

        # OAuth (Infisical)
        kwargs.setdefault("KAKAO_CLIENT_ID", os.getenv("KAKAO_CLIENT_ID"))
        kwargs.setdefault("KAKAO_CLIENT_SECRET", os.getenv("KAKAO_CLIENT_SECRET"))
        kwargs.setdefault("NAVER_CLIENT_ID", os.getenv("NAVER_CLIENT_ID"))
        kwargs.setdefault("NAVER_CLIENT_SECRET", os.getenv("NAVER_CLIENT_SECRET"))
        kwargs.setdefault("GOOGLE_CLIENT_ID", os.getenv("GOOGLE_CLIENT_ID"))
        kwargs.setdefault("GOOGLE_CLIENT_SECRET", os.getenv("GOOGLE_CLIENT_SECRET"))
        kwargs.setdefault("APPLE_CLIENT_ID", os.getenv("APPLE_CLIENT_ID"))
        kwargs.setdefault("APPLE_TEAM_ID", os.getenv("APPLE_TEAM_ID"))
        kwargs.setdefault("APPLE_KEY_ID", os.getenv("APPLE_KEY_ID"))
        kwargs.setdefault("APPLE_PRIVATE_KEY", os.getenv("APPLE_PRIVATE_KEY"))
        kwargs.setdefault("APPLE_SCHEME", os.getenv("APPLE_SCHEME"))

        # External Services
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

        # 환경별 uploads 디렉토리 설정
        if self.ENVIRONMENT in ["local", "development"]:
            # 로컬/개발 환경: services/api/uploads/dev
            api_root = Path(__file__).resolve().parent.parent.parent
            self.UPLOADS_DIR = str(api_root / "uploads" / "dev")
        elif self.ENVIRONMENT in ["staging", "stg"]:
            # 스테이징 환경: /Users/Shared/Projects/PodPod/uploads/stg
            self.UPLOADS_DIR = "/Users/Shared/Projects/PodPod/uploads/stg"
        elif self.ENVIRONMENT in ["production", "prod"]:
            # 프로덕션 환경: /Users/Shared/Projects/PodPod/uploads/prod
            self.UPLOADS_DIR = "/Users/Shared/Projects/PodPod/uploads/prod"
        else:
            # 기본값: services/api/uploads/dev
            api_root = Path(__file__).resolve().parent.parent.parent
            self.UPLOADS_DIR = str(api_root / "uploads" / "dev")

        # uploads 디렉토리가 없으면 생성
        Path(self.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

        # 환경별 logs 디렉토리 설정
        if self.ENVIRONMENT in ["local", "development"]:
            # 로컬/개발 환경: services/api/logs/dev
            api_root = Path(__file__).resolve().parent.parent.parent
            self.LOGS_DIR = str(api_root / "logs" / "dev")
        elif self.ENVIRONMENT in ["staging", "stg"]:
            # 스테이징 환경: /Users/Shared/Projects/PodPod/logs/stg
            self.LOGS_DIR = "/Users/Shared/Projects/PodPod/logs/stg"
        elif self.ENVIRONMENT in ["production", "prod"]:
            # 프로덕션 환경: /Users/Shared/Projects/PodPod/logs/prod
            self.LOGS_DIR = "/Users/Shared/Projects/PodPod/logs/prod"
        else:
            # 기본값: services/api/logs/dev
            api_root = Path(__file__).resolve().parent.parent.parent
            self.LOGS_DIR = str(api_root / "logs" / "dev")

        # logs 디렉토리가 없으면 생성
        Path(self.LOGS_DIR).mkdir(parents=True, exist_ok=True)

        print(f"환경 설정 완료: {self.ENVIRONMENT}")
        print(
            f"데이터베이스: {self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )
        print(f"Base URL: {self.base_url}")
        print(f"Uploads 디렉토리: {self.UPLOADS_DIR}")
        print(f"Logs 디렉토리: {self.LOGS_DIR}")

    @property
    def DATABASE_URL(self) -> str:
        """데이터베이스 URL을 생성합니다."""
        encoded_password = urllib.parse.quote(self.MYSQL_PASSWORD, safe="")
        return f"mysql+aiomysql://{self.MYSQL_USER}:{encoded_password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    # MARK: - OAuth Redirect URIs (자동 생성)

    @property
    def KAKAO_REDIRECT_URI(self) -> str:
        """카카오 OAuth 리다이렉트 URI를 base_url로부터 생성합니다."""
        return f"{self.base_url}/auth/kakao/callback"

    @property
    def NAVER_REDIRECT_URI(self) -> str:
        """네이버 OAuth 리다이렉트 URI를 base_url로부터 생성합니다."""
        return f"{self.base_url}/auth/naver/callback"

    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        """구글 OAuth 리다이렉트 URI를 base_url로부터 생성합니다."""
        return f"{self.base_url}/auth/google/callback"

    @property
    def APPLE_REDIRECT_URI(self) -> str:
        """애플 OAuth 리다이렉트 URI를 base_url로부터 생성합니다."""
        return f"{self.base_url}/auth/apple/callback"

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
settings = Settings()
