from pydantic import BaseModel, Field


class FollowRequest(BaseModel):
    """팔로우 요청 스키마"""

    following_id: int = Field(
        ..., alias="followingId", description="팔로우할 사용자 ID"
    )
