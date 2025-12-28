from datetime import datetime

from pydantic import BaseModel, Field


class FollowInfoDto(BaseModel):
    """팔로우 응답 스키마"""

    follower_id: int = Field(
        ..., alias="followerId", description="팔로우하는 사용자 ID"
    )
    following_id: int = Field(
        ..., alias="followingId", description="팔로우받는 사용자 ID"
    )
    created_at: datetime = Field(..., alias="createdAt", description="팔로우 생성 시간")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
