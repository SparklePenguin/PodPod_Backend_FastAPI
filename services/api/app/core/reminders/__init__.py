"""
PodPod Backend API 리마인더 타입 레지스트리

리마인더 타입은 reminders.json에서 도메인별로 관리됩니다.
동기화는 scripts/sync_reminder_types_to_sheet.py로 수행합니다.
"""

from .registry import (
    REMINDER_TYPES,
    ReminderInfo,
    get_all_reminder_keys,
    get_reminder_by_notification_value,
    get_reminder_info,
    get_reminder_types,
    get_reminders_by_domain,
    reload_reminders,
)

__all__ = [
    "REMINDER_TYPES",
    "ReminderInfo",
    "get_reminder_info",
    "get_reminder_types",
    "get_reminders_by_domain",
    "get_reminder_by_notification_value",
    "get_all_reminder_keys",
    "reload_reminders",
]
