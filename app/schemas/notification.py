"""
FCM 푸시 알림 메시지 스키마
"""

from enum import Enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class PodNotificationType(Enum):
    """팟팟 알림 메시지"""

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
    POD_CANCELED = (
        "😢 [party_name] 모임이 취소되었어요.",
        ["party_name"],
        "pod_id",
    )
    # 8. 신청한 파티 시작 1시간 전 (대상: 사용자)
    POD_START_SOON = (
        "⏰ [party_name] 모임이 한 시간 뒤 시작돼요. 준비되셨나요?",
        ["party_name"],
        "pod_id",
    )
    # 9. 파티 마감 임박 (대상: 파티장)
    POD_LOW_ATTENDANCE = (
        "😢 [party_name] 모임 참여 인원이 부족해요. 다른 유저에게 공유해볼까요?",
        ["party_name"],
        "pod_id",
    )


class PodStatusNotificationType(Enum):
    """팟팟 상태 알림 메시지"""

    # 1. 좋아요 수 10개 이상 달성 (대상: 파티장)
    POD_LIKES_THRESHOLD = (
        "🎉 [party_name] 모임에 좋아요가 10개 이상 쌓였어요!",
        ["party_name"],
        None,
    )
    # 2. 조회수 10회 이상 달성 (대상: 파티장)
    POD_VIEWS_THRESHOLD = (
        "🔥 [party_name]에 관심이 몰리고 있어요. 인기 모임이 될지도 몰라요!",
        ["party_name"],
        None,
    )


class RecommendNotificationType(Enum):
    """추천 알림 메시지"""

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


class ReviewNotificationType(Enum):
    """리뷰 알림 메시지"""

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
        None,
    )
    # 3. 리뷰 미작성자 일주일 리마인드 (대상: 리뷰 미작성자)
    REVIEW_REMINDER_WEEK = (
        "💭 [party_name] 후기가 궁금해요. 어땠는지 들려주세요!",
        ["party_name"],
        None,
    )
    # 4. 내가 참여한 파티에 다른 사람이 후기 작성 (대상: 참여자)
    REVIEW_OTHERS_CREATED = (
        "👀 같은 모임에 참여한 [nickname]님의 후기가 도착했어요!",
        ["nickname"],
        "review_id",
    )


class FollowNotificationType(Enum):
    """팔로우 알림 메시지"""

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


# ========== 알림 스키마 ==========


class NotificationBase(BaseModel):
    """알림 기본 스키마"""

    title: str
    body: str
    notification_type: str
    notification_value: str
    related_id: Optional[str] = None


class NotificationCreate(NotificationBase):
    """알림 생성 스키마"""

    user_id: int


class NotificationResponse(NotificationBase):
    """알림 응답 스키마"""

    id: int
    user_id: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """알림 목록 응답 스키마"""

    total: int
    unread_count: int
    notifications: list[NotificationResponse]


class NotificationUnreadCountResponse(BaseModel):
    """읽지 않은 알림 개수 응답"""

    unread_count: int
