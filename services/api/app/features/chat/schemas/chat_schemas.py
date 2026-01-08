"""
채팅 관련 스키마
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageDto(BaseModel):
    """채팅 메시지 응답 DTO"""

    id: int = Field(description="메시지 ID")
    user_id: int = Field(alias="userId", description="발신자 ID")
    nickname: str | None = Field(default=None, description="발신자 닉네임")
    profile_image: str | None = Field(
        default=None, alias="profileImage", description="발신자 프로필 이미지"
    )
    message: str = Field(description="메시지 내용")
    message_type: str = Field(alias="messageType", description="메시지 타입")
    created_at: datetime = Field(alias="createdAt", description="생성 시간")

    model_config = {"populate_by_name": True}


class ChatRoomDto(BaseModel):
    """채팅방 정보 DTO"""

    id: int | None = Field(default=None, alias="id", description="채팅방 ID")
    pod_id: int | None = Field(default=None, alias="podId", description="파티 ID")
    name: str = Field(description="채팅방 이름")
    cover_url: str | None = Field(
        default=None, alias="coverUrl", description="커버 이미지 URL"
    )
    metadata: dict | None = Field(
        default=None, alias="metadata", description="채팅방 메타데이터 (JSON)"
    )
    member_count: int = Field(alias="memberCount", description="멤버 수")
    last_message: ChatMessageDto | None = Field(
        default=None, alias="lastMessage", description="마지막 메시지"
    )
    unread_count: int = Field(
        default=0, alias="unreadCount", description="읽지 않은 메시지 수"
    )
    created_at: str = Field(alias="createdAt", description="생성 시간")
    updated_at: str = Field(alias="updatedAt", description="수정 시간")

    model_config = {"populate_by_name": True}


class SendMessageRequest(BaseModel):
    """채팅 메시지 전송 요청 DTO"""

    message: str = Field(description="메시지 내용")
    message_type: str = Field(
        default="MESG",
        alias="messageType",
        description="메시지 타입 (MESG, FILE, IMAGE 등)",
    )

    model_config = {"populate_by_name": True}
