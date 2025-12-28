"""
채팅방 목록 DTO
"""

from typing import List

from pydantic import BaseModel, Field

from .chat_room_dto import ChatRoomDto


class ChatRoomListDto(BaseModel):
    """채팅방 목록 응답 DTO"""

    rooms: List[ChatRoomDto] = Field(description="채팅방 목록")
    total_count: int = Field(alias="totalCount", description="총 개수")

    model_config = {"populate_by_name": True}
