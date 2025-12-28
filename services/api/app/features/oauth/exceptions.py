"""
OAuth 도메인 전용 Exception 클래스

이 모듈은 OAuth 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.
"""

from app.core.exceptions import DomainException


class OAuthAuthenticationFailedException(DomainException):
    """OAuth 인증 실패"""

    def __init__(self, provider: str, reason: str | None = None):
        super().__init__(
            error_key="OAUTH_AUTHENTICATION_FAILED",
            format_params={"provider": provider, "reason": reason or ""},
        )
        self.provider = provider
        self.reason = reason


class OAuthTokenInvalidException(DomainException):
    """OAuth 토큰이 유효하지 않은 경우"""

    def __init__(self, provider: str):
        super().__init__(
            error_key="OAUTH_TOKEN_INVALID",
            format_params={"provider": provider},
        )
        self.provider = provider


class OAuthUserInfoFailedException(DomainException):
    """OAuth 사용자 정보 조회 실패"""

    def __init__(self, provider: str):
        super().__init__(
            error_key="OAUTH_USER_INFO_FAILED",
            format_params={"provider": provider},
        )
        self.provider = provider


class OAuthStateInvalidException(DomainException):
    """OAuth state가 유효하지 않은 경우 (CSRF 방지)"""

    def __init__(self):
        super().__init__(error_key="OAUTH_STATE_INVALID")


class OAuthProviderNotSupportedException(DomainException):
    """지원하지 않는 OAuth 제공자"""

    def __init__(self, provider: str):
        super().__init__(
            error_key="OAUTH_PROVIDER_NOT_SUPPORTED",
            format_params={"provider": provider},
        )
        self.provider = provider
