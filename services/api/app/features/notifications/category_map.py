"""알림 이벤트 → 카테고리 매핑"""

from .category import NotificationCategory
from .event import NotificationEvent

# 이벤트별 카테고리 매핑
EVENT_CATEGORY_MAP: dict[NotificationEvent, NotificationCategory] = {
    # ============= Pod Events → POD =============
    NotificationEvent.POD_JOIN_REQUESTED: NotificationCategory.POD,
    NotificationEvent.POD_JOIN_APPROVED: NotificationCategory.POD,
    NotificationEvent.POD_JOIN_REJECTED: NotificationCategory.POD,
    NotificationEvent.POD_MEMBER_JOINED: NotificationCategory.POD,
    NotificationEvent.POD_UPDATED: NotificationCategory.POD,
    NotificationEvent.POD_CONFIRMED: NotificationCategory.POD,
    NotificationEvent.POD_CANCELED: NotificationCategory.POD,
    NotificationEvent.POD_STARTING_SOON: NotificationCategory.POD,
    NotificationEvent.POD_LOW_ATTENDANCE: NotificationCategory.POD,
    NotificationEvent.POD_CANCELED_SOON: NotificationCategory.POD,
    NotificationEvent.POD_COMPLETED: NotificationCategory.POD,
    NotificationEvent.POD_LIKES_THRESHOLD: NotificationCategory.POD,
    NotificationEvent.POD_VIEWS_THRESHOLD: NotificationCategory.POD,
    NotificationEvent.POD_CAPACITY_FULL: NotificationCategory.POD,
    # ============= Review Events → REVIEW =============
    NotificationEvent.REVIEW_CREATED: NotificationCategory.REVIEW,
    NotificationEvent.REVIEW_REMINDER_DAY: NotificationCategory.REVIEW,
    NotificationEvent.REVIEW_REMINDER_WEEK: NotificationCategory.REVIEW,
    NotificationEvent.REVIEW_OTHERS_CREATED: NotificationCategory.REVIEW,
    # ============= User Events → USER =============
    NotificationEvent.USER_FOLLOWED: NotificationCategory.USER,
    NotificationEvent.USER_FOLLOWED_USER_CREATED_POD: NotificationCategory.USER,
    # ============= System Events → SYSTEM =============
    NotificationEvent.SYSTEM_SAVED_POD_DEADLINE: NotificationCategory.SYSTEM,
    NotificationEvent.SYSTEM_SAVED_POD_SPOT_OPENED: NotificationCategory.SYSTEM,
}


def get_category(event: NotificationEvent) -> NotificationCategory:
    """이벤트에 해당하는 카테고리 반환

    Args:
        event: 알림 이벤트

    Returns:
        알림 카테고리
    """
    return EVENT_CATEGORY_MAP.get(event, NotificationCategory.SYSTEM)


def get_category_from_event_value(event_value: str) -> NotificationCategory:
    """이벤트 문자열 값으로 카테고리 반환

    Args:
        event_value: 이벤트 문자열 값 (예: "POD_JOIN_REQUESTED")

    Returns:
        알림 카테고리
    """
    try:
        event = NotificationEvent(event_value)
        return get_category(event)
    except ValueError:
        return NotificationCategory.SYSTEM
