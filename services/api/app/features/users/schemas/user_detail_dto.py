from datetime import datetime

from app.features.follow.schemas import FollowStatsDto
from app.features.users.models import UserState
from pydantic import BaseModel, Field


class UserDetailDto(BaseModel):
    """사용자 상세 정보 응답"""

    id: int = Field()  # 필수값
    email: str | None = Field(default=None)
    username: str | None = Field(default=None)
    nickname: str | None = Field(default=None)
    profile_image: str | None = Field(default=None, alias="profileImage")
    intro: str | None = Field(default=None)
    state: UserState = Field(default=UserState.PREFERRED_ARTISTS)
    tendency_type: str | None = Field(default=None, alias="tendencyType")
    is_following: bool = Field(
        default=False,
        alias="isFollowing",
        description="현재 사용자 기준 팔로우 여부",
    )
    follow_stats: FollowStatsDto = Field(
        ..., alias="followStats", description="팔로우 통계 정보"
    )
    terms_accepted: bool = Field(
        default=False, alias="termsAccepted", description="약관 동의 여부"
    )
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
