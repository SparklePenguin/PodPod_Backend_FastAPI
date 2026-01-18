"""사용자 차단 관련 스키마"""

import datetime

from pydantic import BaseModel, Field


class BlockedUserDto(BaseModel):
    """차단된 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID")
    nickname: str | None = Field(None, description="닉네임")
    profile_image: str | None = Field(
        None, alias="profileImage", description="프로필 이미지 URL"
    )
    intro: str | None = Field(None, description="자기소개")
    blocked_at: datetime.datetime = Field(
        ..., alias="blockedAt", description="차단한 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class BlockInfoDto(BaseModel):
    """사용자 차단 응답 스키마"""

    blocker_id: int = Field(
        ..., alias="blockerId", description="차단을 수행한 사용자 ID"
    )
    blocked_id: int = Field(..., alias="blockedId", description="차단당한 사용자 ID")
    created_at: datetime.datetime = Field(
        ..., alias="createdAt", description="차단 생성 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
