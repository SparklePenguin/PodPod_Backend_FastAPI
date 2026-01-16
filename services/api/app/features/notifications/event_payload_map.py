"""알림 이벤트 → Payload 스키마 매핑

이벤트와 payload의 불일치를 런타임에 검증할 수 있습니다.
"""

from typing import Type

from pydantic import BaseModel

from .event import NotificationEvent
from .payloads.pod import (
    PodCanceledPayload,
    PodCanceledSoonPayload,
    PodCapacityFullPayload,
    PodCompletedPayload,
    PodConfirmedPayload,
    PodJoinApprovedPayload,
    PodJoinRejectedPayload,
    PodJoinRequestedPayload,
    PodLikesThresholdPayload,
    PodLowAttendancePayload,
    PodMemberJoinedPayload,
    PodStartingSoonPayload,
    PodUpdatedPayload,
    PodViewsThresholdPayload,
)
from .payloads.review import (
    ReviewCreatedPayload,
    ReviewOthersCreatedPayload,
    ReviewReminderDayPayload,
    ReviewReminderWeekPayload,
)
from .payloads.system import (
    SystemSavedPodDeadlinePayload,
    SystemSavedPodSpotOpenedPayload,
)
from .payloads.user import (
    UserFollowedPayload,
    UserFollowedUserCreatedPodPayload,
)

# 이벤트별 Payload 스키마 매핑
EVENT_PAYLOAD_SCHEMA: dict[NotificationEvent, Type[BaseModel]] = {
    # ============= Pod Events =============
    NotificationEvent.POD_JOIN_REQUESTED: PodJoinRequestedPayload,
    NotificationEvent.POD_JOIN_APPROVED: PodJoinApprovedPayload,
    NotificationEvent.POD_JOIN_REJECTED: PodJoinRejectedPayload,
    NotificationEvent.POD_MEMBER_JOINED: PodMemberJoinedPayload,
    NotificationEvent.POD_UPDATED: PodUpdatedPayload,
    NotificationEvent.POD_CONFIRMED: PodConfirmedPayload,
    NotificationEvent.POD_CANCELED: PodCanceledPayload,
    NotificationEvent.POD_STARTING_SOON: PodStartingSoonPayload,
    NotificationEvent.POD_LOW_ATTENDANCE: PodLowAttendancePayload,
    NotificationEvent.POD_CANCELED_SOON: PodCanceledSoonPayload,
    NotificationEvent.POD_COMPLETED: PodCompletedPayload,
    NotificationEvent.POD_LIKES_THRESHOLD: PodLikesThresholdPayload,
    NotificationEvent.POD_VIEWS_THRESHOLD: PodViewsThresholdPayload,
    NotificationEvent.POD_CAPACITY_FULL: PodCapacityFullPayload,
    # ============= Review Events =============
    NotificationEvent.REVIEW_CREATED: ReviewCreatedPayload,
    NotificationEvent.REVIEW_REMINDER_DAY: ReviewReminderDayPayload,
    NotificationEvent.REVIEW_REMINDER_WEEK: ReviewReminderWeekPayload,
    NotificationEvent.REVIEW_OTHERS_CREATED: ReviewOthersCreatedPayload,
    # ============= User Events =============
    NotificationEvent.USER_FOLLOWED: UserFollowedPayload,
    NotificationEvent.USER_FOLLOWED_USER_CREATED_POD: UserFollowedUserCreatedPodPayload,
    # ============= System Events =============
    NotificationEvent.SYSTEM_SAVED_POD_DEADLINE: SystemSavedPodDeadlinePayload,
    NotificationEvent.SYSTEM_SAVED_POD_SPOT_OPENED: SystemSavedPodSpotOpenedPayload,
}


def get_payload_schema(event: NotificationEvent) -> Type[BaseModel]:
    """이벤트에 해당하는 payload 스키마 반환

    Args:
        event: 알림 이벤트

    Returns:
        Payload 스키마 클래스

    Raises:
        KeyError: 이벤트에 해당하는 스키마가 없는 경우
    """
    return EVENT_PAYLOAD_SCHEMA[event]


def validate_payload(event: NotificationEvent, payload: dict) -> BaseModel:
    """이벤트에 맞는 payload인지 검증하고 validated 객체 반환

    Args:
        event: 알림 이벤트
        payload: payload 딕셔너리

    Returns:
        검증된 Payload 객체

    Raises:
        ValidationError: payload가 스키마와 맞지 않는 경우
        KeyError: 이벤트에 해당하는 스키마가 없는 경우
    """
    schema = get_payload_schema(event)
    return schema(**payload)
