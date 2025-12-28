"""
채팅방 DTO
"""

from pydantic import BaseModel, Field

from .chat_message_dto import ChatMessageDto


class ChatRoomDto(BaseModel):
    """채팅방 정보 DTO"""

    channel_url: str = Field(alias="channelUrl", description="채널 URL")
    name: str = Field(description="채팅방 이름")
    cover_url: str | None = Field(
        default=None, alias="coverUrl", description="커버 이미지 URL"
    )
    pod_id: int | None = Field(default=None, alias="podId", description="파티 ID")
    pod_title: str | None = Field(
        default=None, alias="podTitle", description="파티 제목"
    )
    member_count: int = Field(alias="memberCount", description="멤버 수")
    last_message: ChatMessageDto | None = Field(
        default=None, alias="lastMessage", description="마지막 메시지"
    )
    unread_count: int = Field(
        default=0, alias="unreadCount", description="읽지 않은 메시지 수"
    )
    created_at: str = Field(alias="createdAt", description="생성 시간")

    model_config = {"populate_by_name": True}
