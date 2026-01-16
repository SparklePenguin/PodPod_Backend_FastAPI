"""알림 카테고리 정의"""

from enum import Enum


class NotificationCategory(str, Enum):
    """알림 카테고리"""

    POD = "POD"  # 파티 관련 알림
    REVIEW = "REVIEW"  # 리뷰 관련 알림
    USER = "USER"  # 유저 관련 알림 (팔로우 포함)
    SYSTEM = "SYSTEM"  # 시스템 알림 (추천 등)
