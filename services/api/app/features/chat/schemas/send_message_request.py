"""
채팅 메시지 전송 요청
"""

from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    """채팅 메시지 전송 요청 DTO"""

    message: str = Field(description="메시지 내용")
    message_type: str = Field(
        default="MESG",
        alias="messageType",
        description="메시지 타입 (MESG, FILE, IMAGE 등)",
    )

    model_config = {"populate_by_name": True}
