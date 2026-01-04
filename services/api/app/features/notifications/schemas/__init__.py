"""Notifications feature schemas"""

from .notification_schemas import (
    FollowNotiSubType,
    FollowNotificationType,
    NotificationCategory,
    NotificationResponse,
    NotificationUnreadCountResponse,
    NotificationType,
    PodNotiSubType,
    PodNotificationType,
    PodStatusNotiSubType,
    PodStatusNotificationType,
    RecommendNotiSubType,
    RecommendNotificationType,
    ReviewNotiSubType,
    ReviewNotificationType,
    get_notification_category,
    get_notification_main_type,
)

__all__ = [
    # Notification Types
    "NotificationType",
    "NotificationCategory",
    # Notification Sub Types
    "PodNotiSubType",
    "PodStatusNotiSubType",
    "RecommendNotiSubType",
    "ReviewNotiSubType",
    "FollowNotiSubType",
    # Legacy Names (하위 호환성)
    "PodNotificationType",
    "PodStatusNotificationType",
    "RecommendNotificationType",
    "ReviewNotificationType",
    "FollowNotificationType",
    # Responses
    "NotificationResponse",
    "NotificationUnreadCountResponse",
    # Utils
    "get_notification_category",
    "get_notification_main_type",
]
