from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class FollowRequest(BaseModel):
    """팔로우 요청 스키마"""

    following_id: int = Field(
        ...,
        serialization_alias="followingId",
        description="팔로우할 사용자 ID",
        examples=[1],
    )


class FollowResponse(BaseModel):
    """팔로우 응답 스키마"""

    follower_id: int = Field(
        ...,
        serialization_alias="followerId",
        description="팔로우하는 사용자 ID",
        examples=[1],
    )
    following_id: int = Field(
        ...,
        serialization_alias="followingId",
        description="팔로우받는 사용자 ID",
        examples=[2],
    )
    created_at: datetime = Field(
        ..., serialization_alias="createdAt", description="팔로우 생성 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class SimpleUserDto(BaseModel):
    """간단한 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID", examples=[1])
    nickname: str = Field(..., description="닉네임", examples=["홍길동"])
    profile_image: str = Field(
        ..., serialization_alias="profileImage", description="프로필 이미지 URL"
    )
    intro: str = Field(..., description="자기소개", examples=["안녕하세요!"])
    tendency_type: str = Field(
        ...,
        serialization_alias="tendencyType",
        description="덕메 성향 타입",
        examples=["ACTIVE"],
    )
    is_following: bool = Field(
        default=False,
        serialization_alias="isFollowing",
        description="팔로우 여부",
        examples=[False],
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowListResponse(BaseModel):
    """팔로우 리스트 응답 스키마"""

    users: List[SimpleUserDto] = Field(..., description="팔로우 사용자 목록")
    total_count: int = Field(
        ..., serialization_alias="totalCount", description="총 팔로우 수", examples=[10]
    )
    page: int = Field(..., description="현재 페이지", examples=[1])
    size: int = Field(..., description="페이지 크기", examples=[20])
    has_next: bool = Field(
        ...,
        serialization_alias="hasNext",
        description="다음 페이지 존재 여부",
        examples=[True],
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowStatsResponse(BaseModel):
    """팔로우 통계 응답 스키마"""

    following_count: int = Field(
        ...,
        serialization_alias="followingCount",
        description="팔로우하는 수",
        examples=[10],
    )
    followers_count: int = Field(
        ..., serialization_alias="followersCount", description="팔로워 수", examples=[5]
    )
    is_following: bool = Field(
        ...,
        serialization_alias="isFollowing",
        description="팔로우 여부",
        examples=[True],
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowNotificationStatusResponse(BaseModel):
    """팔로우 알림 설정 상태 응답 스키마"""

    following_id: int = Field(
        ...,
        serialization_alias="followingId",
        description="팔로우한 사용자 ID",
        examples=[2],
    )
    notification_enabled: bool = Field(
        ...,
        serialization_alias="notificationEnabled",
        description="알림 활성화 여부",
        examples=[True],
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class FollowNotificationUpdateRequest(BaseModel):
    """팔로우 알림 설정 변경 요청 스키마"""

    following_id: int = Field(
        ...,
        serialization_alias="followingId",
        description="팔로우한 사용자 ID",
        examples=[2],
    )
    notification_enabled: bool = Field(
        ...,
        serialization_alias="notificationEnabled",
        description="알림 활성화 여부",
        examples=[True],
    )

    model_config = {
        "populate_by_name": True,
    }
