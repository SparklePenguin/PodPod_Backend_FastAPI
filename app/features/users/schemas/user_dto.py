import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.features.follow.schemas import FollowStatsResponse
from app.features.users.models import UserState


class UserDto(BaseModel):
    """사용자 정보 응답"""

    id: int = Field(serialization_alias="id")  # 필수값
    email: Optional[str] = Field(default=None, serialization_alias="email")
    username: Optional[str] = Field(default=None, serialization_alias="username")
    nickname: Optional[str] = Field(default=None, serialization_alias="nickname")
    profile_image: Optional[str] = Field(
        default=None, serialization_alias="profileImage"
    )
    intro: Optional[str] = Field(default=None, serialization_alias="intro")
    state: UserState = Field(
        default=UserState.PREFERRED_ARTISTS, serialization_alias="state"
    )  # 사용자 온보딩 상태
    tendency_type: Optional[str] = Field(
        default=None, serialization_alias="tendencyType"
    )  # 성향 타입
    is_following: bool = Field(
        default=False,
        serialization_alias="isFollowing",
        description="현재 사용자 기준 팔로우 여부",
        examples=[False],
    )
    follow_stats: Optional[FollowStatsResponse] = Field(
        default=None, serialization_alias="followStats", description="팔로우 통계 정보"
    )
    terms_accepted: bool = Field(
        default=False, serialization_alias="termsAccepted", description="약관 동의 여부"
    )
    created_at: Optional[datetime.datetime] = Field(
        default=None, serialization_alias="createdAt"
    )
    updated_at: Optional[datetime.datetime] = Field(
        default=None, serialization_alias="updatedAt"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }


class UserDtoInternal(BaseModel):
    """내부용 사용자 정보 응답 (모든 정보 포함)"""

    id: int = Field(serialization_alias="id")  # 필수값
    email: Optional[str] = Field(default=None, serialization_alias="email")
    username: Optional[str] = Field(default=None, serialization_alias="username")
    nickname: Optional[str] = Field(default=None, serialization_alias="nickname")
    profile_image: Optional[str] = Field(
        default=None, serialization_alias="profileImage"
    )
    intro: Optional[str] = Field(default=None, serialization_alias="intro")
    hashed_password: Optional[str] = Field(
        default=None, serialization_alias="hashedPassword"
    )
    state: UserState = Field(
        default=UserState.PREFERRED_ARTISTS, serialization_alias="state"
    )  # 사용자 온보딩 상태
    is_active: bool = Field(serialization_alias="isActive")  # 필수값
    auth_provider: Optional[str] = Field(
        default=None, serialization_alias="authProvider"
    )
    auth_provider_id: Optional[str] = Field(
        default=None, serialization_alias="authProviderId"
    )
    created_at: Optional[datetime.datetime] = Field(
        default=None, serialization_alias="createdAt"
    )
    updated_at: Optional[datetime.datetime] = Field(
        default=None, serialization_alias="updatedAt"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }
