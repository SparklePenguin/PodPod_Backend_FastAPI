from pydantic import BaseModel, Field


class FollowStatsDto(BaseModel):
    """팔로우 통계 응답 스키마"""

    following_count: int = Field(
        ..., alias="followingCount", description="팔로우하는 수"
    )
    followers_count: int = Field(..., alias="followersCount", description="팔로워 수")
    is_following: bool = Field(..., alias="isFollowing", description="팔로우 여부")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
