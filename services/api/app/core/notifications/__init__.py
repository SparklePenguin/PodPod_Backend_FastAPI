"""Core notifications module - runtime notification configuration loader"""

from .notification_registry import (
    NotificationInfo,
    get_notification_info,
    get_message_template,
    render_message,
    get_related_id_type,
    get_category,
    is_reminder_event,
    reload_notifications,
    get_all_events,
    get_all_notifications,
)

__all__ = [
    "NotificationInfo",
    "get_notification_info",
    "get_message_template",
    "render_message",
    "get_related_id_type",
    "get_category",
    "is_reminder_event",
    "reload_notifications",
    "get_all_events",
    "get_all_notifications",
]
