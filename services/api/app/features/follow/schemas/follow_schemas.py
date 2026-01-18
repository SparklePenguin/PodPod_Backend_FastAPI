"""팔로우 관련 스키마"""

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


class FollowRequest(BaseModel):
    """팔로우 요청 스키마"""

    following_id: int = Field(
        ..., alias="followingId", description="팔로우할 사용자 ID"
    )


class FollowNotificationStatusDto(BaseModel):
    """팔로우 알림 설정 상태 응답 스키마"""

    following_id: int = Field(
        ..., alias="followingId", description="팔로우한 사용자 ID"
    )
    notification_enabled: bool = Field(
        ..., alias="notificationEnabled", description="알림 활성화 여부"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowNotificationUpdateRequest(BaseModel):
    """팔로우 알림 설정 변경 요청 스키마"""

    following_id: int = Field(
        ..., alias="followingId", description="팔로우한 사용자 ID"
    )
    notification_enabled: bool = Field(
        ..., alias="notificationEnabled", description="알림 활성화 여부"
    )

    model_config = {
        "populate_by_name": True,
    }
