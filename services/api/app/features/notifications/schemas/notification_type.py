from enum import Enum


class NotificationType(str, Enum):
    """알림 메인 타입"""

    POD = "POD"  # 파티 알림
    POD_STATUS = "POD_STATUS"  # 파티 상태 알림
    RECOMMEND = "RECOMMEND"  # 추천 알림
    REVIEW = "REVIEW"  # 리뷰 알림
    FOLLOW = "FOLLOW"  # 팔로우 알림
