"""리뷰 관련 알림 Payload 정의"""

from pydantic import Field

from .base import PodRef, ReviewRef, UserRef


class ReviewCreatedPayload(UserRef, PodRef, ReviewRef):
    """리뷰 등록 알림 payload (대상: 파티장)"""

    pass


class ReviewReminderDayPayload(PodRef):
    """리뷰 작성 유도 (1일 후) 알림 payload (대상: 참여자)"""

    pass


class ReviewReminderWeekPayload(PodRef):
    """리뷰 작성 리마인드 (1주일 후) 알림 payload (대상: 리뷰 미작성자)"""

    pass


class ReviewOthersCreatedPayload(UserRef, ReviewRef):
    """다른 참여자 리뷰 작성 알림 payload (대상: 같은 파티 참여자)"""

    pod_id: int = Field(description="파티 ID")
