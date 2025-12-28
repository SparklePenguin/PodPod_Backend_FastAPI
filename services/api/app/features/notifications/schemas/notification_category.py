from enum import Enum

from .notification_type import NotificationType

# 메인 타입과 카테고리 매칭
NOTIFICATION_MAIN_TYPE_CATEGORY_MAP = {
    NotificationType.POD: "POD",
    NotificationType.POD_STATUS: "POD",
    NotificationType.RECOMMEND: "POD",
    NotificationType.REVIEW: "COMMUNITY",
    NotificationType.FOLLOW: "COMMUNITY",
}

# 문자열 타입과 카테고리 매핑
NOTIFICATION_TYPE_CATEGORY_MAP = {
    # 파티 관련
    "PodNotiSubType": "POD",
    "PodStatusNotiSubType": "POD",
    "RecommendNotiSubType": "POD",
    # 커뮤니티 관련
    "FollowNotiSubType": "COMMUNITY",
    "ReviewNotiSubType": "COMMUNITY",
    # 레거시 이름 지원
    "PodNotificationType": "POD",
    "PodStatusNotificationType": "POD",
    "RecommendNotificationType": "POD",
    "FollowNotificationType": "COMMUNITY",
    "ReviewNotificationType": "COMMUNITY",
}


class NotificationCategory(str, Enum):
    """알림 카테고리"""

    POD = "POD"  # 파티 관련 알림
    COMMUNITY = "COMMUNITY"  # 커뮤니티 관련 알림 (팔로우, 리뷰 등)
    NOTICE = "NOTICE"  # 공지/리마인드 알림


def get_notification_category(type: str) -> str:
    """
    알림 타입으로 카테고리 반환

    Args:
        type: 알림 타입 (예: PodNotificationType, FollowNotificationType) 또는 NotificationType enum 값 (예: POD, POD_STATUS)

    Returns:
        카테고리 (POD, COMMUNITY, NOTICE)
    """
    # 먼저 클래스명으로 찾기 시도
    if type in NOTIFICATION_TYPE_CATEGORY_MAP:
        return NOTIFICATION_TYPE_CATEGORY_MAP[type]

    # 클래스명이 아니면 NotificationType enum 값으로 찾기 시도
    try:
        notification_type_enum = NotificationType(type)
        if notification_type_enum in NOTIFICATION_MAIN_TYPE_CATEGORY_MAP:
            return NOTIFICATION_MAIN_TYPE_CATEGORY_MAP[notification_type_enum]
    except ValueError:
        pass

    # 둘 다 아니면 기본값 반환
    return NotificationCategory.POD.value
