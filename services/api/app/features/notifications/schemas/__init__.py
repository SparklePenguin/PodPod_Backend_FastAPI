"""Notifications feature schemas"""

from .notification_schemas import (
    # Schemas
    NotificationBase,
    NotificationDto,
    NotificationUnreadCountResponse,
    # Category
    NotificationCategory,
    # Event
    NotificationEvent,
    PodEvent,
    ReviewEvent,
    UserEvent,
    SystemEvent,
    # Category mapping
    get_category,
    get_category_from_event_value,
    # Utils
    to_upper_camel_case,
)

__all__ = [
    # Schemas
    "NotificationBase",
    "NotificationDto",
    "NotificationUnreadCountResponse",
    # Category
    "NotificationCategory",
    # Event
    "NotificationEvent",
    "PodEvent",
    "ReviewEvent",
    "UserEvent",
    "SystemEvent",
    # Category mapping
    "get_category",
    "get_category_from_event_value",
    # Utils
    "to_upper_camel_case",
]
