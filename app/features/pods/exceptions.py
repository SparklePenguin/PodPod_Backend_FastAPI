"""
Pods 도메인 전용 Exception 클래스

이 모듈은 Pods 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.

사용법:
    1. Google Sheets에 에러 키 등록 (예: POD_NOT_FOUND)
    2. 이 파일에서 Exception 클래스 정의 (error_key만 지정)
    3. 서비스에서 예외 발생 시 자동으로 메시지 로드
"""

from app.core.exceptions import DomainException


class PodNotFoundException(DomainException):
    """파티를 찾을 수 없는 경우"""

    def __init__(self, pod_id: int):
        super().__init__(
            error_key="POD_NOT_FOUND",
            format_params={"pod_id": pod_id},
        )
        self.pod_id = pod_id


class PodFullException(DomainException):
    """파티 정원이 가득 찬 경우"""

    def __init__(self, pod_id: int, max_members: int, current_members: int):
        super().__init__(
            error_key="POD_FULL",
            format_params={
                "pod_id": pod_id,
                "max_members": max_members,
                "current_members": current_members,
            },
        )
        self.pod_id = pod_id
        self.max_members = max_members
        self.current_members = current_members


class PodAlreadyJoinedException(DomainException):
    """이미 참여한 파티인 경우"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="ALREADY_MEMBER",  # 기존 error_codes.py에 이미 정의됨
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class PodApplicationAlreadyExistsException(DomainException):
    """이미 신청한 파티인 경우"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="ALREADY_APPLIED",  # 기존 error_codes.py에 이미 정의됨
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class PodNotHostException(DomainException):
    """파티 호스트가 아닌 경우 (권한 없음)"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="NOT_POD_HOST",
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class PodClosedException(DomainException):
    """종료된 파티인 경우"""

    def __init__(self, pod_id: int):
        super().__init__(
            error_key="POD_CLOSED",
            format_params={"pod_id": pod_id},
        )
        self.pod_id = pod_id


class PodApplicationNotFoundException(DomainException):
    """파티 신청을 찾을 수 없는 경우"""

    def __init__(self, application_id: int):
        super().__init__(
            error_key="POD_APPLICATION_NOT_FOUND",
            format_params={"application_id": application_id},
        )
        self.application_id = application_id


class InvalidPodStatusException(DomainException):
    """유효하지 않은 파티 상태인 경우"""

    def __init__(self, pod_id: int, current_status: str, required_status: str):
        super().__init__(
            error_key="INVALID_POD_STATUS",
            format_params={
                "pod_id": pod_id,
                "current_status": current_status,
                "required_status": required_status,
            },
        )
        self.pod_id = pod_id
        self.current_status = current_status
        self.required_status = required_status


class PodReviewAlreadyExistsException(DomainException):
    """이미 리뷰를 작성한 경우"""

    def __init__(self, pod_id: int, user_id: int):
        super().__init__(
            error_key="POD_REVIEW_ALREADY_EXISTS",
            format_params={"pod_id": pod_id, "user_id": user_id},
        )
        self.pod_id = pod_id
        self.user_id = user_id


class PodReviewNotAllowedException(DomainException):
    """리뷰 작성 권한이 없는 경우 (파티에 참여하지 않았거나 종료되지 않음)"""

    def __init__(self, pod_id: int, user_id: int, reason: str):
        super().__init__(
            error_key="POD_REVIEW_NOT_ALLOWED",
            format_params={"pod_id": pod_id, "user_id": user_id, "reason": reason},
        )
        self.pod_id = pod_id
        self.user_id = user_id
        self.reason = reason
