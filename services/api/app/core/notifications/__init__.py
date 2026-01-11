"""
PodPod Backend API 알림 타입 레지스트리

알림 타입은 notifications.json에서 도메인별로 관리됩니다.
동기화는 scripts/sync_notification_types_to_sheet.py로 수행합니다.
"""

from .registry import (
    NOTIFICATION_TYPES,
    NotificationTypeInfo,
    get_all_notification_keys,
    get_notification_type_info,
    get_notification_types,
    get_notifications_by_category,
    get_notifications_by_domain,
    get_notifications_by_type,
    reload_notifications,
)

__all__ = [
    "NOTIFICATION_TYPES",
    "NotificationTypeInfo",
    "get_notification_type_info",
    "get_notification_types",
    "get_notifications_by_domain",
    "get_notifications_by_category",
    "get_notifications_by_type",
    "get_all_notification_keys",
    "reload_notifications",
]
