"""
PodPod Backend API 알림 타입 레지스트리

알림 타입은 notifications.json에서 도메인별로 관리됩니다.
동기화는 scripts/sync_notification_types_to_sheet.py로 수행합니다.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# notifications.json 경로
NOTIFICATIONS_JSON_PATH = Path(__file__).parent / "notifications.json"

# 알림 타입 (notifications.json에서 로드됨)
NOTIFICATION_TYPES: Dict[str, Dict[str, Any]] = {}


@dataclass
class NotificationTypeInfo:
    """알림 타입 정보를 담는 객체"""

    notification_key: str
    code: int
    message_template: str
    placeholders: List[str]
    related_id_key: str
    notification_type: str
    category: str
    target: str
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


def _load_notifications_from_json() -> None:
    """notifications.json에서 알림 타입을 로드합니다."""
    global NOTIFICATION_TYPES

    if not NOTIFICATIONS_JSON_PATH.exists():
        print(f"경고: notifications.json 파일을 찾을 수 없습니다: {NOTIFICATIONS_JSON_PATH}")
        return

    try:
        with open(NOTIFICATIONS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 도메인별 구조를 flat하게 변환
        for domain, notifications in data.items():
            for notification_key, notification_data in notifications.items():
                NOTIFICATION_TYPES[notification_key] = notification_data

        print(
            f"notifications.json에서 {len(NOTIFICATION_TYPES)}개의 알림 타입을 로드했습니다."
        )

    except Exception as e:
        print(f"notifications.json 로드 실패: {str(e)}")


# 모듈 로드 시 자동으로 알림 타입 로드
_load_notifications_from_json()


def get_notification_types() -> Dict[str, Dict[str, Any]]:
    """알림 타입 딕셔너리를 반환합니다."""
    return NOTIFICATION_TYPES.copy()


def get_notification_type_info(notification_key: str) -> NotificationTypeInfo:
    """
    알림 키로 알림 타입 정보를 가져옵니다.

    Args:
        notification_key: 알림 키 (예: "POD_JOIN_REQUEST")

    Returns:
        NotificationTypeInfo 객체
    """
    if notification_key not in NOTIFICATION_TYPES:
        raise ValueError(f"Unknown notification key: {notification_key}")

    data = NOTIFICATION_TYPES[notification_key]
    return NotificationTypeInfo(
        notification_key=notification_key,
        code=data["code"],
        message_template=data["message_template"],
        placeholders=data["placeholders"],
        related_id_key=data["related_id_key"],
        notification_type=data["notification_type"],
        category=data["category"],
        target=data["target"],
        description_ko=data["description_ko"],
        description_en=data["description_en"],
        dev_note=data.get("dev_note"),
    )


def get_notifications_by_domain(domain: str) -> Dict[str, Dict[str, Any]]:
    """
    도메인별 알림 타입을 가져옵니다.

    Args:
        domain: 도메인명 (예: "pod", "follow", "review")

    Returns:
        해당 도메인의 알림 딕셔너리
    """
    if not NOTIFICATIONS_JSON_PATH.exists():
        return {}

    with open(NOTIFICATIONS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get(domain, {})


def get_notifications_by_category(category: str) -> Dict[str, NotificationTypeInfo]:
    """
    카테고리별 알림 타입을 가져옵니다.

    Args:
        category: 카테고리 (예: "POD", "COMMUNITY")

    Returns:
        해당 카테고리의 알림 딕셔너리
    """
    result = {}
    for key, data in NOTIFICATION_TYPES.items():
        if data.get("category") == category:
            result[key] = get_notification_type_info(key)
    return result


def get_notifications_by_type(notification_type: str) -> Dict[str, NotificationTypeInfo]:
    """
    메인 타입별 알림을 가져옵니다.

    Args:
        notification_type: 메인 타입 (예: "POD", "FOLLOW", "REVIEW")

    Returns:
        해당 타입의 알림 딕셔너리
    """
    result = {}
    for key, data in NOTIFICATION_TYPES.items():
        if data.get("notification_type") == notification_type:
            result[key] = get_notification_type_info(key)
    return result


def get_all_notification_keys() -> List[str]:
    """모든 알림 키 목록을 반환합니다."""
    return list(NOTIFICATION_TYPES.keys())


def reload_notifications() -> None:
    """notifications.json을 다시 로드합니다."""
    global NOTIFICATION_TYPES
    NOTIFICATION_TYPES.clear()
    _load_notifications_from_json()
