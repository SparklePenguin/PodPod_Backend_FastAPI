"""
Pods 도메인 전용 Exception 클래스

이 모듈은 Pods 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.
"""

from app.core.exceptions import DomainException


class PodNotFoundException(DomainException):
    """파티를 찾을 수 없는 경우"""

    def __init__(self, pod_id: int):
        super().__init__(error_key="POD_NOT_FOUND", format_params={"pod_id": pod_id})
        self.pod_id = pod_id


class NoPodAccessPermissionException(DomainException):
    """파티 접근 권한이 없는 경우"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="NO_POD_ACCESS_PERMISSION",
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class PodAlreadyClosedException(DomainException):
    """이미 처리된 파티인 경우"""

    def __init__(self, pod_id: int):
        super().__init__(
            error_key="POD_ALREADY_CLOSED", format_params={"pod_id": pod_id}
        )
        self.pod_id = pod_id


class PodIsFullException(DomainException):
    """파티가 가득 찬 경우"""

    def __init__(self, pod_id: int):
        super().__init__(error_key="POD_IS_FULL", format_params={"pod_id": pod_id})
        self.pod_id = pod_id


class AlreadyMemberException(DomainException):
    """이미 파티 멤버인 경우"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="ALREADY_MEMBER",
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class AlreadyAppliedException(DomainException):
    """이미 신청한 경우"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="ALREADY_APPLIED",
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class PodAccessDeniedException(DomainException):
    """파티 접근이 거부된 경우"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="POD_ACCESS_DENIED",
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class ReviewAlreadyExistsException(DomainException):
    """이미 후기를 작성한 경우"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="REVIEW_ALREADY_EXISTS",
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class ReviewNotFoundException(DomainException):
    """후기를 찾을 수 없는 경우"""

    def __init__(self, review_id: int):
        super().__init__(
            error_key="REVIEW_NOT_FOUND", format_params={"review_id": review_id}
        )
        self.review_id = review_id


class ReviewPermissionDeniedException(DomainException):
    """후기 수정/삭제 권한이 없는 경우"""

    def __init__(self, review_id: int, user_id: int):
        super().__init__(
            error_key="REVIEW_PERMISSION_DENIED",
            format_params={"review_id": review_id, "user_id": user_id},
        )
        self.review_id = review_id
        self.user_id = user_id


class InvalidImageException(DomainException):
    """이미지가 유효하지 않은 경우"""

    def __init__(self, reason: str | None = None):
        super().__init__(
            error_key="INVALID_IMAGE",
            format_params={"reason": reason or "Invalid image"},
        )
        self.reason = reason


class InvalidPodStatusException(DomainException):
    """파티 상태 값이 유효하지 않은 경우"""

    def __init__(self, status_value: str):
        super().__init__(
            error_key="INVALID_POD_STATUS",
            format_params={"status_value": status_value},
        )
        self.status_value = status_value


class InvalidDateException(DomainException):
    """날짜 형식이 유효하지 않은 경우"""

    def __init__(self, date_string: str | None = None):
        super().__init__(
            error_key="INVALID_DATE",
            format_params={"date_string": date_string or "Invalid date"},
        )
        self.date_string = date_string


class MissingStatusException(DomainException):
    """상태 필드가 누락된 경우"""

    def __init__(self):
        super().__init__(error_key="MISSING_STATUS")


class PodUpdateFailedException(DomainException):
    """파티 업데이트 실패"""

    def __init__(self, pod_id: int):
        super().__init__(
            error_key="POD_UPDATE_FAILED", format_params={"pod_id": pod_id}
        )
        self.pod_id = pod_id
