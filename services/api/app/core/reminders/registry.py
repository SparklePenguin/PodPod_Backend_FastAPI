"""
PodPod Backend API 리마인더 타입 레지스트리

리마인더 타입은 reminders.json에서 도메인별로 관리됩니다.
동기화는 scripts/sync_reminder_types_to_sheet.py로 수행합니다.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# reminders.json 경로
REMINDERS_JSON_PATH = Path(__file__).parent / "reminders.json"

# 리마인더 타입 (reminders.json에서 로드됨)
REMINDER_TYPES: Dict[str, Dict[str, Any]] = {}


@dataclass
class ReminderInfo:
    """리마인더 정보를 담는 객체"""

    reminder_key: str
    code: int
    trigger_hours: int
    trigger_type: str
    target: str
    message_template: str
    placeholders: List[str]
    related_id_key: str
    notification_type: str
    notification_value: str
    category: str
    duplicate_check_hours: int
    description_ko: str
    description_en: str
    dev_note: str | None = None

    def format_message(self, **kwargs) -> str:
        """메시지 템플릿에 값을 채워서 반환"""
        message = self.message_template
        for placeholder in self.placeholders:
            value = kwargs.get(placeholder, "")
            message = message.replace(f"[{placeholder}]", str(value))
        return message


def _load_reminders_from_json() -> None:
    """reminders.json에서 리마인더 타입을 로드합니다."""
    global REMINDER_TYPES

    if not REMINDERS_JSON_PATH.exists():
        print(f"경고: reminders.json 파일을 찾을 수 없습니다: {REMINDERS_JSON_PATH}")
        return

    try:
        with open(REMINDERS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 도메인별 구조를 flat하게 변환
        for domain, reminders in data.items():
            for reminder_key, reminder_data in reminders.items():
                REMINDER_TYPES[reminder_key] = reminder_data

        print(f"reminders.json에서 {len(REMINDER_TYPES)}개의 리마인더 타입을 로드했습니다.")

    except Exception as e:
        print(f"reminders.json 로드 실패: {str(e)}")


# 모듈 로드 시 자동으로 리마인더 타입 로드
_load_reminders_from_json()


def get_reminder_types() -> Dict[str, Dict[str, Any]]:
    """리마인더 타입 딕셔너리를 반환합니다."""
    return REMINDER_TYPES.copy()


def get_reminder_info(reminder_key: str) -> ReminderInfo:
    """
    리마인더 키로 리마인더 정보를 가져옵니다.

    Args:
        reminder_key: 리마인더 키 (예: "REVIEW_REMINDER_DAY")

    Returns:
        ReminderInfo 객체
    """
    if reminder_key not in REMINDER_TYPES:
        raise ValueError(f"Unknown reminder key: {reminder_key}")

    data = REMINDER_TYPES[reminder_key]
    return ReminderInfo(
        reminder_key=reminder_key,
        code=data["code"],
        trigger_hours=data["trigger_hours"],
        trigger_type=data["trigger_type"],
        target=data["target"],
        message_template=data["message_template"],
        placeholders=data["placeholders"],
        related_id_key=data["related_id_key"],
        notification_type=data["notification_type"],
        notification_value=data["notification_value"],
        category=data["category"],
        duplicate_check_hours=data["duplicate_check_hours"],
        description_ko=data["description_ko"],
        description_en=data["description_en"],
        dev_note=data.get("dev_note"),
    )


def get_reminders_by_domain(domain: str) -> Dict[str, Dict[str, Any]]:
    """
    도메인별 리마인더 타입을 가져옵니다.

    Args:
        domain: 도메인명 (예: "review_reminders", "pod_reminders")

    Returns:
        해당 도메인의 리마인더 딕셔너리
    """
    if not REMINDERS_JSON_PATH.exists():
        return {}

    with open(REMINDERS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get(domain, {})


def get_reminder_by_notification_value(notification_value: str) -> ReminderInfo | None:
    """
    notification_value로 리마인더 정보를 가져옵니다.

    Args:
        notification_value: 알림 값 (예: "REVIEW_REMINDER_DAY")

    Returns:
        ReminderInfo 객체 또는 None
    """
    for reminder_key, data in REMINDER_TYPES.items():
        if data.get("notification_value") == notification_value:
            return get_reminder_info(reminder_key)
    return None


def get_all_reminder_keys() -> List[str]:
    """모든 리마인더 키 목록을 반환합니다."""
    return list(REMINDER_TYPES.keys())


def reload_reminders() -> None:
    """reminders.json을 다시 로드합니다."""
    global REMINDER_TYPES
    REMINDER_TYPES.clear()
    _load_reminders_from_json()
