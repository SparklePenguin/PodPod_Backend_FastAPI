"""알림 관련 스키마"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_serializer

if TYPE_CHECKING:
    pass

from app.features.pods.schemas import PodDto
from app.features.users.schemas import UserDto


# ============= Base =============
class NotificationBase(BaseModel):
    """알림 기본 스키마"""

    title: str = Field()
    body: str = Field()
    type: str = Field()
    value: str = Field()
    related_id: int | None = Field(default=None, alias="relatedId")


# ============= Notification Types =============
class NotificationType(str, Enum):
    """알림 메인 타입"""

    POD = "POD"  # 파티 알림
    POD_STATUS = "POD_STATUS"  # 파티 상태 알림
    RECOMMEND = "RECOMMEND"  # 추천 알림
    REVIEW = "REVIEW"  # 리뷰 알림
    FOLLOW = "FOLLOW"  # 팔로우 알림


class NotificationCategory(str, Enum):
    """알림 카테고리"""

    POD = "POD"  # 파티 관련 알림
    COMMUNITY = "COMMUNITY"  # 커뮤니티 관련 알림 (팔로우, 리뷰 등)
    NOTICE = "NOTICE"  # 공지/리마인드 알림


# ============= Notification Sub Types =============
class PodNotiSubType(Enum):
    """파티 알림 서브 타입"""

    # 1. 파티 참여 요청 (대상: 파티장)
    POD_JOIN_REQUEST = (
        "[nickname]님이 모임에 참여를 요청했어요. 확인해 보세요!",
        ["nickname"],
        "pod_id",
    )
    # 2. 참여 요청 승인 (대상: 요청자)
    POD_REQUEST_APPROVED = (
        "👋 [party_name] 참여가 확정되었어요! 채팅방에서 인사 나눠보세요.",
        ["party_name"],
        "pod_id",
    )
    # 3. 참여 요청 거절 (대상: 요청자)
    POD_REQUEST_REJECTED = (
        "😢 아쉽게도 [party_name] 참여가 어렵게 되었어요. 다른 모임도 둘러보세요.",
        ["party_name"],
        "pod_id",
    )
    # 4. 파티에 새로운 유저 참여 (대상: 기존 파티원들)
    POD_NEW_MEMBER = (
        "👋 새로운 파티원 [nickname]님이 [party_name] 모임에 함께하게 되었어요!",
        ["nickname", "party_name"],
        "pod_id",
    )
    # 5. 파티 내용 수정 (대상: 파티장 & 파티원)
    POD_UPDATED = (
        "🛠️ [party_name] 모임 정보가 변경되었어요. 지금 확인해 보세요.",
        ["party_name"],
        "pod_id",
    )
    # 6. 파티 확정 (대상: 파티원)
    POD_CONFIRMED = (
        "✅ 모임이 드디어 확정! [party_name]에 함께할 준비 되셨죠?",
        ["party_name"],
        "pod_id",
    )
    # 7. 파티 취소 (대상: 파티원)
    POD_CANCELED = ("😢 [party_name] 모임이 취소되었어요.", ["party_name"], "pod_id")
    # 8. 신청한 파티 시작 1시간 전 (대상: 사용자)
    POD_START_SOON = (
        "⏰ [party_name] 모임이 한 시간 뒤 시작돼요. 준비되셨나요?",
        ["party_name"],
        "pod_id",
    )
    # 9. 파티 마감 임박 (대상: 파티장)
    POD_LOW_ATTENDANCE = (
        "😢 [party_name] 오늘 파티가 확정되지 않으면 취소돼요. 시간이 더 필요하다면 일정을 수정할 수 있어요!",
        ["party_name"],
        "pod_id",
    )
    # 10. 파티 취소 임박 (대상: 파티장)
    POD_CANCELED_SOON = (
        "😢 [party_name] 팟티가 곧 취소돼요!",
        ["party_name"],
        "pod_id",
    )


class PodStatusNotiSubType(Enum):
    """파티 상태 알림 서브 타입"""

    # 1. 좋아요 수 10개 이상 달성 (대상: 파티장)
    POD_LIKES_THRESHOLD = (
        "🎉 [party_name] 모임에 좋아요가 10개 이상 쌓였어요!",
        ["party_name"],
        "pod_id",
    )
    # 2. 조회수 10회 이상 달성 (대상: 파티장)
    POD_VIEWS_THRESHOLD = (
        "🔥 [party_name]에 관심이 몰리고 있어요. 인기 모임이 될지도 몰라요!",
        ["party_name"],
        "pod_id",
    )
    # 3. 파티 완료 (대상: 참여자들)
    POD_COMPLETED = (
        "🎉 [party_name] 모임이 완료되었습니다! 즐거운 시간 보내셨나요?",
        ["party_name"],
        "pod_id",
    )
    # 4. 파티 정원 가득 참 (대상: 파티장)
    POD_CAPACITY_FULL = (
        "👋 [party_name] 참여 인원이 모두 모였어요!",
        ["party_name"],
        "pod_id",
    )


class RecommendNotiSubType(Enum):
    """추천 알림 서브 타입"""

    # 1. 좋아요한 파티 마감 임박 (1일 전, 대상: 사용자)
    SAVED_POD_DEADLINE = (
        "🚨 [party_name] 곧 마감돼요! 신청 놓칠지도 몰라요 😥",
        ["party_name"],
        "pod_id",
    )
    # 2. 좋아요한 파티에 자리가 생겼을 때 (대상: 사용자)
    SAVED_POD_SPOT_OPENED = (
        "🎉 [party_name]에 자리가 생겼어요! 지금 신청해 보세요.",
        ["party_name"],
        "pod_id",
    )


class ReviewNotiSubType(Enum):
    """리뷰 알림 서브 타입"""

    # 1. 리뷰 등록됨 (대상: 모임 참여자)
    REVIEW_CREATED = (
        "📝 [nickname]님이 [party_name]에 대한 리뷰를 남겼어요!",
        ["nickname", "party_name"],
        "review_id",
    )
    # 2. 모임 종료 후 1일 후 리뷰 유도 (대상: 참여자)
    REVIEW_REMINDER_DAY = (
        "😊 오늘 [party_name] 어떠셨나요? 소중한 리뷰를 남겨보세요!",
        ["party_name"],
        "pod_id",
    )
    # 3. 리뷰 미작성자 일주일 리마인드 (대상: 리뷰 미작성자)
    REVIEW_REMINDER_WEEK = (
        "💭 [party_name] 후기가 궁금해요. 어땠는지 들려주세요!",
        ["party_name"],
        "pod_id",
    )
    # 4. 내가 참여한 파티에 다른 사람이 후기 작성 (대상: 참여자)
    REVIEW_OTHERS_CREATED = (
        "👀 같은 모임에 참여한 [nickname]님의 후기가 도착했어요!",
        ["nickname"],
        "review_id",
    )


class FollowNotiSubType(Enum):
    """팔로우 알림 서브 타입"""

    # 1. 나를 팔로잉함 (대상: 팔로우된 유저)
    FOLLOWED_BY_USER = (
        "👋 [nickname]님이 당신을 팔로우했어요! 새로운 만남을 기대해 볼까요?",
        ["nickname"],
        "follow_user_id",
    )
    # 2. 내가 팔로잉한 유저가 파티 생성 (대목: 팔로워)
    FOLLOWED_USER_CREATED_POD = (
        "🎉 [nickname]님이 새로운 모임 [party_name]을 만들었어요!",
        ["nickname", "party_name"],
        "pod_id",
    )


# 하위 호환성: 레거시 이름
PodNotificationType = PodNotiSubType
PodStatusNotificationType = PodStatusNotiSubType
RecommendNotificationType = RecommendNotiSubType
ReviewNotificationType = ReviewNotiSubType
FollowNotificationType = FollowNotiSubType


# ============= Notification Category Mapping =============
# 메인 타입과 카테고리 매칭
NOTIFICATION_MAIN_TYPE_CATEGORY_MAP = {
    NotificationType.POD: "POD",
    NotificationType.POD_STATUS: "POD",
    NotificationType.RECOMMEND: "POD",
    NotificationType.REVIEW: "COMMUNITY",
    NotificationType.FOLLOW: "COMMUNITY",
}

# 문자열 타입과 카테고리 매핑
NOTIFICATION_TYPE_CATEGORY_MAP = {
    # 파티 관련
    "PodNotiSubType": "POD",
    "PodStatusNotiSubType": "POD",
    "RecommendNotiSubType": "POD",
    # 커뮤니티 관련
    "FollowNotiSubType": "COMMUNITY",
    "ReviewNotiSubType": "COMMUNITY",
    # 레거시 이름 지원
    "PodNotificationType": "POD",
    "PodStatusNotificationType": "POD",
    "RecommendNotificationType": "POD",
    "FollowNotificationType": "COMMUNITY",
    "ReviewNotificationType": "COMMUNITY",
}


def get_notification_category(type: str) -> str:
    """
    알림 타입으로 카테고리 반환

    Args:
        type: 알림 타입 (예: PodNotificationType, FollowNotificationType) 또는 NotificationType enum 값 (예: POD, POD_STATUS)

    Returns:
        카테고리 (POD, COMMUNITY, NOTICE)
    """
    # 먼저 클래스명으로 찾기 시도
    if type in NOTIFICATION_TYPE_CATEGORY_MAP:
        return NOTIFICATION_TYPE_CATEGORY_MAP[type]

    # 클래스명이 아니면 NotificationType enum 값으로 찾기 시도
    try:
        notification_type_enum = NotificationType(type)
        if notification_type_enum in NOTIFICATION_MAIN_TYPE_CATEGORY_MAP:
            return NOTIFICATION_MAIN_TYPE_CATEGORY_MAP[notification_type_enum]
    except ValueError:
        pass

    # 둘 다 아니면 기본값 반환
    return NotificationCategory.POD.value


def get_notification_main_type(notification_type: str) -> str:
    """
    알림 타입 클래스명을 NotificationType enum 값으로 변환

    Args:
        notification_type: 알림 타입 클래스명 (예: PodNotificationType, FollowNotificationType)

    Returns:
        NotificationType enum 값 (예: POD, FOLLOW)
    """
    type_mapping = {
        "PodNotificationType": NotificationType.POD,
        "PodStatusNotificationType": NotificationType.POD_STATUS,
        "RecommendNotificationType": NotificationType.RECOMMEND,
        "ReviewNotificationType": NotificationType.REVIEW,
        "FollowNotificationType": NotificationType.FOLLOW,
    }
    return type_mapping.get(notification_type, NotificationType.POD).value


def to_upper_camel_case(snake_str: str) -> str:
    """
    UPPER_SNAKE_CASE를 UpperCamelCase로 변환

    Args:
        snake_str: UPPER_SNAKE_CASE 문자열 (예: POD_JOIN_REQUEST)

    Returns:
        UpperCamelCase 문자열 (예: PodJoinRequest)
    """
    components = snake_str.lower().split("_")
    return "".join(x.title() for x in components)


# ============= Response Schemas =============
class NotificationDto(NotificationBase):
    """알림 응답 스키마"""

    id: int = Field()
    related_user: UserDto | None = Field(
        default=None,
        alias="relatedUser",
        description="관련 유저 (Optional)",
    )
    related_pod: PodDto | None = Field(
        default=None,
        alias="relatedPod",
        description="관련 파티 (Optional)",
    )
    category: NotificationCategory = Field(
        description="알림 카테고리 (POD, COMMUNITY, NOTICE)",
    )
    is_read: bool = Field(alias="isRead")
    read_at: datetime | None = Field(
        default=None, alias="readAt", description="읽은 시간 (Optional)"
    )
    created_at: datetime = Field(alias="createdAt", description="생성 시간")

    @field_serializer("read_at", "created_at")
    def serialize_datetime(self, dt: datetime | None, _info) -> int | None:
        """datetime을 timestamp(밀리초)로 변환"""
        if dt is None:
            return None
        # naive datetime을 UTC로 인식 (DB에서 읽은 값은 UTC로 저장된 naive datetime)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)  # JavaScript/Flutter는 밀리초 단위 사용

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NotificationUnreadCountResponse(BaseModel):
    """읽지 않은 알림 개수 응답"""

    unread_count: int = Field(alias="unreadCount")

    model_config = {"populate_by_name": True}


# Forward reference 해결을 위해 PodDto import 후 모델 재빌드
NotificationDto.model_rebuild()
