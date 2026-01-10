"""Notifications feature schemas"""

from .notification_schemas import (
    FollowNotificationType,
    FollowNotiSubType,
    NotificationCategory,
    NotificationDto,
    NotificationType,
    NotificationUnreadCountResponse,
    PodNotificationType,
    PodNotiSubType,
    PodStatusNotificationType,
    PodStatusNotiSubType,
    RecommendNotificationType,
    RecommendNotiSubType,
    ReviewNotificationType,
    ReviewNotiSubType,
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
    "NotificationDto",
    "NotificationUnreadCountResponse",
    # Utils
    "get_notification_category",
    "get_notification_main_type",
]
