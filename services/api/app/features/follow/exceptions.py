"""
Follow 도메인 전용 Exception 클래스

이 모듈은 Follow 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.
"""

from app.core.exceptions import DomainException


class FollowFailedException(DomainException):
    """팔로우에 실패한 경우"""

    def __init__(self, follower_id: int, following_id: int):
        super().__init__(
            error_key="FOLLOW_FAILED",
            format_params={"follower_id": follower_id, "following_id": following_id},
        )
        self.follower_id = follower_id
        self.following_id = following_id


class FollowInvalidException(DomainException):
    """팔로우 정보가 올바르지 않은 경우"""

    def __init__(self, reason: str | None = None):
        super().__init__(
            error_key="FOLLOW_INVALID",
            format_params={"reason": reason or "Invalid follow information"},
        )
        self.reason = reason


class FollowNotFoundException(DomainException):
    """팔로우 관계를 찾을 수 없는 경우"""

    def __init__(self, follower_id: int, following_id: int):
        super().__init__(
            error_key="FOLLOW_NOT_FOUND",
            format_params={"follower_id": follower_id, "following_id": following_id},
        )
        self.follower_id = follower_id
        self.following_id = following_id
