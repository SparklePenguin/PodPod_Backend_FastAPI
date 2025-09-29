from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FollowRequest(BaseModel):
    """팔로우 요청 스키마"""

    followingId: int = Field(..., description="팔로우할 사용자 ID", example=1)


class FollowResponse(BaseModel):
    """팔로우 응답 스키마"""

    followerId: int = Field(
        ..., alias="follower_id", description="팔로우하는 사용자 ID", example=1
    )
    followingId: int = Field(
        ..., alias="following_id", description="팔로우받는 사용자 ID", example=2
    )
    createdAt: datetime = Field(..., alias="created_at", description="팔로우 생성 시간")

    model_config = {"from_attributes": True}


class UserFollowDto(BaseModel):
    """팔로우 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID", example=1)
    nickname: Optional[str] = Field(None, description="닉네임", example="홍길동")
    profileImage: Optional[str] = Field(
        None, alias="profile_image", description="프로필 이미지 URL"
    )
    intro: Optional[str] = Field(None, description="자기소개", example="안녕하세요!")
    createdAt: datetime = Field(..., alias="created_at", description="팔로우 생성 시간")

    model_config = {"from_attributes": True}


class FollowListResponse(BaseModel):
    """팔로우 리스트 응답 스키마"""

    users: List[UserFollowDto] = Field(..., description="팔로우 사용자 목록")
    totalCount: int = Field(
        ..., alias="total_count", description="총 팔로우 수", example=10
    )
    page: int = Field(..., description="현재 페이지", example=1)
    size: int = Field(..., description="페이지 크기", example=20)
    hasNext: bool = Field(
        ..., alias="has_next", description="다음 페이지 존재 여부", example=True
    )


class FollowStatsResponse(BaseModel):
    """팔로우 통계 응답 스키마"""

    followingCount: int = Field(
        ..., alias="following_count", description="팔로우하는 수", example=10
    )
    followersCount: int = Field(
        ..., alias="followers_count", description="팔로워 수", example=5
    )
    isFollowing: bool = Field(
        ..., alias="is_following", description="팔로우 여부", example=True
    )
