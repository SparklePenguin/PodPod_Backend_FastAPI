from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FollowRequest(BaseModel):
    """팔로우 요청 스키마"""

    following_id: int = Field(
        ..., alias="followingId", description="팔로우할 사용자 ID", example=1
    )


class FollowResponse(BaseModel):
    """팔로우 응답 스키마"""

    follower_id: int = Field(
        ..., alias="followerId", description="팔로우하는 사용자 ID", example=1
    )
    following_id: int = Field(
        ..., alias="followingId", description="팔로우받는 사용자 ID", example=2
    )
    created_at: datetime = Field(..., alias="createdAt", description="팔로우 생성 시간")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class SimpleUserDto(BaseModel):
    """간단한 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID", example=1)
    nickname: str = Field(..., description="닉네임", example="홍길동")
    profile_image: str = Field(
        ..., alias="profileImage", description="프로필 이미지 URL"
    )
    intro: str = Field(..., description="자기소개", example="안녕하세요!")
    tendency_type: str = Field(
        ..., alias="tendencyType", description="덕메 성향 타입", example="ACTIVE"
    )
    is_following: bool = Field(
        default=False, alias="isFollowing", description="팔로우 여부", example=False
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowListResponse(BaseModel):
    """팔로우 리스트 응답 스키마"""

    users: List[SimpleUserDto] = Field(..., description="팔로우 사용자 목록")
    total_count: int = Field(
        ..., alias="totalCount", description="총 팔로우 수", example=10
    )
    page: int = Field(..., description="현재 페이지", example=1)
    size: int = Field(..., description="페이지 크기", example=20)
    has_next: bool = Field(
        ..., alias="hasNext", description="다음 페이지 존재 여부", example=True
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowStatsResponse(BaseModel):
    """팔로우 통계 응답 스키마"""

    following_count: int = Field(
        ..., alias="followingCount", description="팔로우하는 수", example=10
    )
    followers_count: int = Field(
        ..., alias="followersCount", description="팔로워 수", example=5
    )
    is_following: bool = Field(
        ..., alias="isFollowing", description="팔로우 여부", example=True
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowNotificationStatusResponse(BaseModel):
    """팔로우 알림 설정 상태 응답 스키마"""

    following_id: int = Field(
        ..., alias="followingId", description="팔로우한 사용자 ID", example=2
    )
    notification_enabled: bool = Field(
        ..., alias="notificationEnabled", description="알림 활성화 여부", example=True
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowNotificationUpdateRequest(BaseModel):
    """팔로우 알림 설정 변경 요청 스키마"""

    following_id: int = Field(
        ..., alias="followingId", description="팔로우한 사용자 ID", example=2
    )
    notification_enabled: bool = Field(
        ..., alias="notificationEnabled", description="알림 활성화 여부", example=True
    )

    model_config = {
        "populate_by_name": True,
    }
