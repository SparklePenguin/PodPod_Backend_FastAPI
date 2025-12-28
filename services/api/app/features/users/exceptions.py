"""
Users 도메인 전용 Exception 클래스

이 모듈은 Users 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.
"""

from app.core.exceptions import DomainException


class UserNotFoundException(DomainException):
    """사용자를 찾을 수 없는 경우"""

    def __init__(self, user_id: int):
        super().__init__(error_key="USER_NOT_FOUND", format_params={"user_id": user_id})
        self.user_id = user_id


class EmailRequiredException(DomainException):
    """이메일이 필수인데 제공되지 않은 경우"""

    def __init__(self):
        super().__init__(error_key="EMAIL_REQUIRED")


class EmailAlreadyExistsException(DomainException):
    """이미 존재하는 이메일인 경우"""

    def __init__(self, email: str):
        super().__init__(
            error_key="EMAIL_ALREADY_EXISTS", format_params={"email": email}
        )
        self.email = email


class SameOAuthProviderExistsException(DomainException):
    """같은 OAuth 제공자의 계정이 이미 존재하는 경우"""

    def __init__(self, provider: str):
        super().__init__(
            error_key="SAME_OAUTH_PROVIDER_EXISTS", format_params={"provider": provider}
        )
        self.provider = provider


class ArtistNotFoundException(DomainException):
    """아티스트를 찾을 수 없는 경우 (선호 아티스트 관련)"""

    def __init__(self, artist_id: int):
        super().__init__(
            error_key="ARTIST_NOT_FOUND", format_params={"artist_id": artist_id}
        )
        self.artist_id = artist_id
