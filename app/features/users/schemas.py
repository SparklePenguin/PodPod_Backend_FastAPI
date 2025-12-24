import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.features.follow.schemas import FollowStatsResponse
from app.features.users.models import UserState

from .random_profile_image import RandomProfileImageResponse


# - MARK: 사용자 정보 응답
class UserDto(BaseModel):
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


# - MARK: 내부용 사용자 정보 응답 (모든 정보 포함)
class UserDtoInternal(BaseModel):
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


# - MARK: 프로필 업데이트 요청
class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, serialization_alias="nickname")
    profile_image: Optional[str] = Field(
        default=None, serialization_alias="profileImage"
    )
    intro: Optional[str] = Field(default=None, serialization_alias="intro")

    model_config = {
        "populate_by_name": True,
    }


# - MARK: 멀티파트 프로필 업데이트 요청
class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, serialization_alias="nickname")
    intro: Optional[str] = Field(default=None, serialization_alias="intro")

    model_config = {"populate_by_name": True}


# - MARK: 선호 아티스트 요청
class UpdatePreferredArtistsRequest(BaseModel):
    artist_ids: List[int] = Field(default=[], serialization_alias="artistIds")

    model_config = {
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }


# - MARK: 약관 동의 요청
class AcceptTermsRequest(BaseModel):
    terms_accepted: bool = Field(
        default=True, serialization_alias="termsAccepted", description="약관 동의 여부"
    )

    model_config = {"populate_by_name": True}


# - MARK: 차단 관련 스키마
class BlockedUserDto(BaseModel):
    """차단된 사용자 정보 DTO"""

    id: int = Field(..., description="사용자 ID", examples=[1])
    nickname: Optional[str] = Field(None, description="닉네임", examples=["홍길동"])
    profile_image: Optional[str] = Field(
        None, serialization_alias="profileImage", description="프로필 이미지 URL"
    )
    intro: Optional[str] = Field(None, description="자기소개", examples=["안녕하세요!"])
    blocked_at: datetime.datetime = Field(
        ..., serialization_alias="blockedAt", description="차단한 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class BlockUserResponse(BaseModel):
    """사용자 차단 응답 스키마"""

    blocker_id: int = Field(
        ...,
        serialization_alias="blockerId",
        description="차단을 수행한 사용자 ID",
        examples=[1],
    )
    blocked_id: int = Field(
        ...,
        serialization_alias="blockedId",
        description="차단당한 사용자 ID",
        examples=[2],
    )
    created_at: datetime.datetime = Field(
        ..., serialization_alias="createdAt", description="차단 생성 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class UserNotificationSettingsDto(BaseModel):
    """사용자 알림 설정 응답 스키마"""

    id: int = Field(..., serialization_alias="id", description="설정 ID")
    user_id: int = Field(..., serialization_alias="userId", description="사용자 ID")

    # 알림 카테고리별 설정
    wake_up_alarm: bool = Field(
        default=True, serialization_alias="wakeUpAlarm", description="기상 알림"
    )
    bus_alert: bool = Field(
        default=True, serialization_alias="busAlert", description="버스 알림"
    )
    party_alert: bool = Field(
        default=True, serialization_alias="partyAlert", description="파티 알림"
    )
    community_alert: bool = Field(
        default=True, serialization_alias="communityAlert", description="커뮤니티 알림"
    )
    product_alarm: bool = Field(
        default=True, serialization_alias="productAlarm", description="상품 알림"
    )

    # 방해금지 설정
    do_not_disturb_enabled: bool = Field(
        default=False,
        serialization_alias="doNotDisturbEnabled",
        description="방해금지 모드",
    )
    start_time: Optional[int] = Field(
        None,
        serialization_alias="startTime",
        description="방해금지 시작 시간 (timestamp)",
    )
    end_time: Optional[int] = Field(
        None,
        serialization_alias="endTime",
        description="방해금지 종료 시간 (timestamp)",
    )

    # 마케팅 설정
    marketing_enabled: bool = Field(
        default=False,
        serialization_alias="marketingEnabled",
        description="마케팅 알림 수신",
    )

    model_config = {"from_attributes": True, "populate_by_name": True}


class UpdateUserNotificationSettingsRequest(BaseModel):
    """사용자 알림 설정 수정 요청 스키마"""

    wake_up_alarm: Optional[bool] = Field(
        None, serialization_alias="wakeUpAlarm", description="기상 알림"
    )
    bus_alert: Optional[bool] = Field(
        None, serialization_alias="busAlert", description="버스 알림"
    )
    party_alert: Optional[bool] = Field(
        None, serialization_alias="partyAlert", description="파티 알림"
    )
    community_alert: Optional[bool] = Field(
        None, serialization_alias="communityAlert", description="커뮤니티 알림"
    )
    product_alarm: Optional[bool] = Field(
        None, serialization_alias="productAlarm", description="상품 알림"
    )
    do_not_disturb_enabled: Optional[bool] = Field(
        None, serialization_alias="doNotDisturbEnabled", description="방해금지 모드"
    )
    start_time: Optional[int] = Field(
        None,
        serialization_alias="startTime",
        description="방해금지 시작 시간 (timestamp)",
    )
    end_time: Optional[int] = Field(
        None,
        serialization_alias="endTime",
        description="방해금지 종료 시간 (timestamp)",
    )
    marketing_enabled: Optional[bool] = Field(
        None, serialization_alias="marketingEnabled", description="마케팅 알림 수신"
    )

    model_config = {"populate_by_name": True}


__all__ = [
    "UserDto",
    "UpdateProfileRequest",
    "UpdatePreferredArtistsRequest",
    "UserNotificationSettingsDto",
    "RandomProfileImageResponse",
]
