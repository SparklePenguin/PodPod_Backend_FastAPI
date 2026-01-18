"""알림 관련 스키마"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.features.notifications.category import NotificationCategory
from app.features.notifications.category_map import (
    get_category,
    get_category_from_event_value,
)
from app.features.notifications.event import NotificationEvent
from app.features.notifications.events import (
    PodEvent,
    ReviewEvent,
    SystemEvent,
    UserEvent,
)
from app.features.pods.schemas import PodDto
from app.features.users.schemas import UserDto


# ============= Base =============
class NotificationBase(BaseModel):
    """알림 기본 스키마"""

    title: str = Field()
    body: str = Field()
    event: str = Field(description="알림 이벤트 (예: POD_JOIN_REQUESTED)")
    related_id: int | None = Field(default=None, alias="relatedId")


# ============= Response Schemas =============
class NotificationDto(NotificationBase):
    """알림 응답 스키마"""

    id: int = Field()
    related_user: UserDto | None = Field(
        default=None,
        alias="relatedUser",
        description="관련 유저 (Optional)",
    )
    related_pod: PodDto | None = Field(
        default=None,
        alias="relatedPod",
        description="관련 파티 (Optional)",
    )
    category: NotificationCategory = Field(
        description="알림 카테고리 (POD, REVIEW, USER, SYSTEM)",
    )
    is_read: bool = Field(alias="isRead")
    read_at: datetime | None = Field(
        default=None, alias="readAt", description="읽은 시간 (Optional)"
    )
    created_at: datetime = Field(alias="createdAt", description="생성 시간")

    @field_serializer("read_at", "created_at")
    def serialize_datetime(self, dt: datetime | None, _info) -> int | None:
        """datetime을 timestamp(밀리초)로 변환"""
        if dt is None:
            return None
        # naive datetime을 UTC로 인식 (DB에서 읽은 값은 UTC로 저장된 naive datetime)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)  # JavaScript/Flutter는 밀리초 단위 사용

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NotificationUnreadCountResponse(BaseModel):
    """읽지 않은 알림 개수 응답"""

    unread_count: int = Field(alias="unreadCount")

    model_config = {"populate_by_name": True}


# ============= Utility Functions =============
def to_upper_camel_case(snake_str: str) -> str:
    """UPPER_SNAKE_CASE를 UpperCamelCase로 변환

    Args:
        snake_str: UPPER_SNAKE_CASE 문자열 (예: POD_JOIN_REQUESTED)

    Returns:
        UpperCamelCase 문자열 (예: PodJoinRequested)
    """
    components = snake_str.lower().split("_")
    return "".join(x.title() for x in components)


# ============= Re-exports =============
# 새로운 모듈에서 re-export (하위 호환성 및 편의성)
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


# Forward reference 해결을 위해 PodDto import 후 모델 재빌드
NotificationDto.model_rebuild()
