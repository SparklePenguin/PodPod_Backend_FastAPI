from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.features.pods.schemas import PodDto
from pydantic import BaseModel, ConfigDict, Field, field_serializer

if TYPE_CHECKING:
    pass
from app.features.users.schemas import UserDto

from .notification_base import NotificationBase
from .notification_category import NotificationCategory


class NotificationResponse(NotificationBase):
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
        description="알림 카테고리 (POD, COMMUNITY, NOTICE)",
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


# Forward reference 해결을 위해 PodDto import 후 모델 재빌드
NotificationResponse.model_rebuild()
