"""파티(Pod) 관련 알림 Payload 정의"""

from pydantic import Field

from .base import PodRef, UserRef


# ============= 참여 관련 =============
class PodJoinRequestedPayload(UserRef):
    """파티 참여 요청 알림 payload (대상: 파티장)"""

    pod_id: int = Field(description="파티 ID")


class PodJoinApprovedPayload(PodRef):
    """참여 요청 승인 알림 payload (대상: 요청자)"""

    pass


class PodJoinRejectedPayload(PodRef):
    """참여 요청 거절 알림 payload (대상: 요청자)"""

    pass


class PodMemberJoinedPayload(PodRef, UserRef):
    """새 멤버 참여 알림 payload (대상: 기존 파티원들)"""

    pass


# ============= 파티 상태 변경 =============
class PodUpdatedPayload(PodRef):
    """파티 내용 수정 알림 payload (대상: 파티장 & 파티원)"""

    pass


class PodConfirmedPayload(PodRef):
    """파티 확정 알림 payload (대상: 파티원)"""

    pass


class PodCanceledPayload(PodRef):
    """파티 취소 알림 payload (대상: 파티원)"""

    pass


class PodStartingSoonPayload(PodRef):
    """파티 시작 임박 알림 payload (대상: 참여자)"""

    pass


class PodLowAttendancePayload(PodRef):
    """파티 마감 임박 알림 payload (대상: 파티장)"""

    pass


class PodCanceledSoonPayload(PodRef):
    """파티 취소 임박 알림 payload (대상: 파티장)"""

    pass


class PodCompletedPayload(PodRef):
    """파티 완료 알림 payload (대상: 참여자들)"""

    pass


# ============= 파티 인기/상태 알림 =============
class PodLikesThresholdPayload(PodRef):
    """좋아요 10개 달성 알림 payload (대상: 파티장)"""

    pass


class PodViewsThresholdPayload(PodRef):
    """조회수 10회 달성 알림 payload (대상: 파티장)"""

    pass


class PodCapacityFullPayload(PodRef):
    """정원 가득 참 알림 payload (대상: 파티장)"""

    pass
