"""시스템 알림 Payload 정의 (추천 등)"""

from .base import PodRef


class SystemSavedPodDeadlinePayload(PodRef):
    """좋아요한 파티 마감 임박 알림 payload (대상: 좋아요한 유저)"""

    pass


class SystemSavedPodSpotOpenedPayload(PodRef):
    """좋아요한 파티 자리 오픈 알림 payload (대상: 좋아요한 유저)"""

    pass
