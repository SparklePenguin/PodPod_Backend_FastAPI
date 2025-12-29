from pydantic import BaseModel, Field


class FollowNotificationStatusDto(BaseModel):
    """팔로우 알림 설정 상태 응답 스키마"""

    following_id: int = Field(
        ..., alias="followingId", description="팔로우한 사용자 ID"
    )
    notification_enabled: bool = Field(
        ..., alias="notificationEnabled", description="알림 활성화 여부"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
