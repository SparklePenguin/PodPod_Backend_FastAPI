"""사용자 관련 스키마"""

from datetime import datetime
from typing import List

from app.features.follow.schemas import FollowStatsDto
from app.features.users.models import UserState
from pydantic import BaseModel, Field


class UserDto(BaseModel):
    """간단한 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID")
    nickname: str | None = Field(None, description="닉네임")
    profile_image: str | None = Field(
        None, alias="profileImage", description="프로필 이미지 URL"
    )
    intro: str | None = Field(None, description="자기소개")
    tendency_type: str | None = Field(None, alias="tendencyType", description="덕메 성향 타입")
    is_following: bool = Field(
        default=False, alias="isFollowing", description="팔로우 여부"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


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


class UpdateUserRequest(BaseModel):
    """멀티파트 프로필 업데이트 요청"""

    nickname: str | None = Field(default=None)
    intro: str | None = Field(default=None)

    model_config = {"populate_by_name": True}


class UpdateProfileRequest(BaseModel):
    """프로필 업데이트 요청"""

    nickname: str | None = Field(default=None)
    profile_image: str | None = Field(default=None, alias="profileImage")
    intro: str | None = Field(default=None)

    model_config = {
        "populate_by_name": True,
    }


class AcceptTermsRequest(BaseModel):
    """약관 동의 요청"""

    terms_accepted: bool = Field(
        default=True, alias="termsAccepted", description="약관 동의 여부"
    )

    model_config = {"populate_by_name": True}


class UpdatePreferredArtistsRequest(BaseModel):
    """선호 아티스트 요청"""

    artist_ids: List[int] = Field(default=[], alias="artistIds")

    model_config = {
        "populate_by_name": True,
    }


class RandomProfileImageDto(BaseModel):
    """랜덤 프로필 이미지 응답 DTO"""

    image_url: str = Field(
        ...,
        alias="imageUrl",
        description="랜덤으로 선택된 프로필 이미지 URL",
    )
    image_name: str = Field(..., alias="imageName", description="이미지 파일명")

    model_config = {"from_attributes": True, "populate_by_name": True}
