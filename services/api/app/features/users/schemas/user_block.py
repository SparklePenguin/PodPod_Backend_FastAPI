import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BlockedUserDto(BaseModel):
    """차단된 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID", examples=[1])
    nickname: Optional[str] = Field(None, description="닉네임", examples=["홍길동"])
    profile_image: Optional[str] = Field(
        None, serialization_alias="profileImage", description="프로필 이미지 URL"
    )
    intro: Optional[str] = Field(None, description="자기소개", examples=["안녕하세요!"])
    blocked_at: datetime.datetime = Field(
        ..., serialization_alias="blockedAt", description="차단한 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class BlockUserResponse(BaseModel):
    """사용자 차단 응답 스키마"""

    blocker_id: int = Field(
        ...,
        serialization_alias="blockerId",
        description="차단을 수행한 사용자 ID",
        examples=[1],
    )
    blocked_id: int = Field(
        ...,
        serialization_alias="blockedId",
        description="차단당한 사용자 ID",
        examples=[2],
    )
    created_at: datetime.datetime = Field(
        ..., serialization_alias="createdAt", description="차단 생성 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
