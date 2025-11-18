import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.user_state import UserState
from app.schemas.follow import FollowStatsResponse


# - MARK: 사용자 정보 응답
class UserDto(BaseModel):
    id: int = Field(alias="id")  # 필수값
    email: Optional[str] = Field(default=None, alias="email")
    username: Optional[str] = Field(default=None, alias="username")
    nickname: Optional[str] = Field(default=None, alias="nickname")
    profile_image: Optional[str] = Field(default=None, alias="profileImage")
    intro: Optional[str] = Field(default=None, alias="intro")
    state: UserState = Field(
        default=UserState.PREFERRED_ARTISTS, alias="state"
    )  # 사용자 온보딩 상태
    tendency_type: Optional[str] = Field(
        default=None, alias="tendencyType"
    )  # 성향 타입
    is_following: bool = Field(
        default=False,
        alias="isFollowing",
        description="현재 사용자 기준 팔로우 여부",
        example=False,
    )
    follow_stats: Optional[FollowStatsResponse] = Field(
        default=None, alias="followStats", description="팔로우 통계 정보"
    )
    created_at: Optional[datetime.datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime.datetime] = Field(default=None, alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }


# - MARK: 내부용 사용자 정보 응답 (모든 정보 포함)
class UserDtoInternal(BaseModel):
    id: int = Field(alias="id")  # 필수값
    email: Optional[str] = Field(default=None, alias="email")
    username: Optional[str] = Field(default=None, alias="username")
    nickname: Optional[str] = Field(default=None, alias="nickname")
    profile_image: Optional[str] = Field(default=None, alias="profileImage")
    intro: Optional[str] = Field(default=None, alias="intro")
    hashed_password: Optional[str] = Field(default=None, alias="hashedPassword")
    state: UserState = Field(
        default=UserState.PREFERRED_ARTISTS, alias="state"
    )  # 사용자 온보딩 상태
    is_active: bool = Field(alias="isActive")  # 필수값
    auth_provider: Optional[str] = Field(default=None, alias="authProvider")
    auth_provider_id: Optional[str] = Field(default=None, alias="authProviderId")
    created_at: Optional[datetime.datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime.datetime] = Field(default=None, alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }


# - MARK: 프로필 업데이트 요청
class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, alias="nickname")
    profile_image: Optional[str] = Field(default=None, alias="profileImage")
    intro: Optional[str] = Field(default=None, alias="intro")

    model_config = {
        "populate_by_name": True,
    }


# - MARK: 멀티파트 프로필 업데이트 요청
class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, alias="nickname")
    intro: Optional[str] = Field(default=None, alias="intro")

    model_config = {"populate_by_name": True}


# - MARK: 선호 아티스트 요청
class UpdatePreferredArtistsRequest(BaseModel):
    artist_ids: List[int] = Field(default=[], alias="artistIds")

    model_config = {
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }


# - MARK: 차단 관련 스키마
class BlockedUserDto(BaseModel):
    """차단된 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID", example=1)
    nickname: Optional[str] = Field(None, description="닉네임", example="홍길동")
    profile_image: Optional[str] = Field(
        None, alias="profileImage", description="프로필 이미지 URL"
    )
    intro: Optional[str] = Field(None, description="자기소개", example="안녕하세요!")
    blocked_at: datetime.datetime = Field(
        ..., alias="blockedAt", description="차단한 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class BlockUserResponse(BaseModel):
    """사용자 차단 응답 스키마"""

    blocker_id: int = Field(
        ..., alias="blockerId", description="차단을 수행한 사용자 ID", example=1
    )
    blocked_id: int = Field(
        ..., alias="blockedId", description="차단당한 사용자 ID", example=2
    )
    created_at: datetime.datetime = Field(
        ..., alias="createdAt", description="차단 생성 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
