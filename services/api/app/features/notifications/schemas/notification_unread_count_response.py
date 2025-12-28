from pydantic import BaseModel, Field


class NotificationUnreadCountResponse(BaseModel):
    """읽지 않은 알림 개수 응답"""

    unread_count: int = Field(alias="unreadCount")

    model_config = {"populate_by_name": True}
