"""
채팅 메시지 DTO
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageDto(BaseModel):
    """채팅 메시지 응답 DTO"""

    id: int = Field(description="메시지 ID")
    channel_url: str = Field(alias="channelUrl", description="채널 URL")
    user_id: int = Field(alias="userId", description="발신자 ID")
    nickname: str | None = Field(default=None, description="발신자 닉네임")
    profile_image: str | None = Field(
        default=None, alias="profileImage", description="발신자 프로필 이미지"
    )
    message: str = Field(description="메시지 내용")
    message_type: str = Field(alias="messageType", description="메시지 타입")
    created_at: datetime = Field(alias="createdAt", description="생성 시간")

    model_config = {"populate_by_name": True}
