"""알림 레지스트리 - notifications.json 기반 런타임 로더

Google Sheets에서 관리하는 알림 설정을 로드하여 사용합니다.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from app.features.notifications.category import NotificationCategory
from app.features.notifications.event import NotificationEvent

logger = logging.getLogger(__name__)

# notifications.json 경로
NOTIFICATIONS_JSON_PATH = Path(__file__).parent / "notifications.json"


@dataclass(frozen=True)
class NotificationInfo:
    """알림 정보"""
    
    event: str
    category: NotificationCategory
    message_template: str
    placeholders: list[str]
    related_id_type: str
    is_reminder: bool
    refs: list[str]
    target: str
    description: str


# 알림 레지스트리 (싱글톤)
_NOTIFICATION_REGISTRY: dict[str, NotificationInfo] = {}
_LOADED = False


def _load_notifications() -> None:
    """notifications.json 로드"""
    global _NOTIFICATION_REGISTRY, _LOADED
    
    if _LOADED:
        return
    
    if not NOTIFICATIONS_JSON_PATH.exists():
        logger.warning(
            f"notifications.json 파일이 없습니다: {NOTIFICATIONS_JSON_PATH}\n"
            "  → sync_notification_types_to_sheet.py 실행 필요"
        )
        _LOADED = True
        return
    
    try:
        with open(NOTIFICATIONS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for event_key, info in data.items():
            try:
                category = NotificationCategory(info.get("category", "SYSTEM"))
            except ValueError:
                category = NotificationCategory.SYSTEM
            
            _NOTIFICATION_REGISTRY[event_key] = NotificationInfo(
                event=event_key,
                category=category,
                message_template=info.get("message_template", ""),
                placeholders=info.get("placeholders", []),
                related_id_type=info.get("related_id_type", "pod_id"),
                is_reminder=info.get("meta", {}).get("is_reminder", False),
                refs=info.get("ref", []),
                target=info.get("target", ""),
                description=info.get("description", ""),
            )
        
        logger.info(f"notifications.json 로드 완료: {len(_NOTIFICATION_REGISTRY)}개 이벤트")
        _LOADED = True
        
    except Exception as e:
        logger.error(f"notifications.json 로드 실패: {e}")
        _LOADED = True


def get_notification_info(event: NotificationEvent | str) -> NotificationInfo | None:
    """이벤트 정보 조회
    
    Args:
        event: NotificationEvent 또는 이벤트 문자열
        
    Returns:
        NotificationInfo 또는 None
    """
    _load_notifications()
    
    event_key = event.value if isinstance(event, NotificationEvent) else event
    return _NOTIFICATION_REGISTRY.get(event_key)


def get_message_template(event: NotificationEvent | str) -> str:
    """메시지 템플릿 조회
    
    Args:
        event: NotificationEvent 또는 이벤트 문자열
        
    Returns:
        메시지 템플릿 문자열 (없으면 빈 문자열)
    """
    info = get_notification_info(event)
    return info.message_template if info else ""


def render_message(event: NotificationEvent | str, **kwargs: str) -> str:
    """메시지 렌더링
    
    Args:
        event: NotificationEvent 또는 이벤트 문자열
        **kwargs: placeholder 값들 (nickname="홍길동", party_name="맛집탐방" 등)
        
    Returns:
        렌더링된 메시지
    """
    info = get_notification_info(event)
    if not info:
        logger.warning(f"알림 정보 없음: {event}")
        return ""
    
    message = info.message_template
    
    for placeholder in info.placeholders:
        if placeholder in kwargs:
            message = message.replace(f"[{placeholder}]", str(kwargs[placeholder]))
    
    return message


def get_related_id_type(event: NotificationEvent | str) -> str:
    """related_id 타입 조회
    
    Args:
        event: NotificationEvent 또는 이벤트 문자열
        
    Returns:
        related_id 타입 (pod_id, review_id, user_id 등)
    """
    info = get_notification_info(event)
    return info.related_id_type if info else "pod_id"


def get_category(event: NotificationEvent | str) -> NotificationCategory:
    """카테고리 조회
    
    Args:
        event: NotificationEvent 또는 이벤트 문자열
        
    Returns:
        NotificationCategory
    """
    info = get_notification_info(event)
    return info.category if info else NotificationCategory.SYSTEM


def is_reminder_event(event: NotificationEvent | str) -> bool:
    """리마인더 이벤트 여부
    
    Args:
        event: NotificationEvent 또는 이벤트 문자열
        
    Returns:
        리마인더 여부
    """
    info = get_notification_info(event)
    return info.is_reminder if info else False


def reload_notifications() -> None:
    """notifications.json 다시 로드 (개발/테스트용)"""
    global _NOTIFICATION_REGISTRY, _LOADED
    _NOTIFICATION_REGISTRY = {}
    _LOADED = False
    _load_notifications()


def get_all_events() -> list[str]:
    """모든 이벤트 키 목록"""
    _load_notifications()
    return list(_NOTIFICATION_REGISTRY.keys())


def get_all_notifications() -> dict[str, NotificationInfo]:
    """모든 알림 정보"""
    _load_notifications()
    return _NOTIFICATION_REGISTRY.copy()
