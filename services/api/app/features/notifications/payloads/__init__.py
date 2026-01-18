"""알림 Payload 모듈"""

from .base import PodRef, ReviewRef, UserRef
from .pod import (
    PodCapacityFullPayload,
    PodCanceledPayload,
    PodCanceledSoonPayload,
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
from .review import (
    ReviewCreatedPayload,
    ReviewOthersCreatedPayload,
    ReviewReminderDayPayload,
    ReviewReminderWeekPayload,
)
from .system import (
    SystemSavedPodDeadlinePayload,
    SystemSavedPodSpotOpenedPayload,
)
from .user import (
    UserFollowedPayload,
    UserFollowedUserCreatedPodPayload,
)

__all__ = [
    # Base Refs
    "PodRef",
    "UserRef",
    "ReviewRef",
    # Pod Payloads
    "PodJoinRequestedPayload",
    "PodJoinApprovedPayload",
    "PodJoinRejectedPayload",
    "PodMemberJoinedPayload",
    "PodUpdatedPayload",
    "PodConfirmedPayload",
    "PodCanceledPayload",
    "PodStartingSoonPayload",
    "PodLowAttendancePayload",
    "PodCanceledSoonPayload",
    "PodCompletedPayload",
    "PodLikesThresholdPayload",
    "PodViewsThresholdPayload",
    "PodCapacityFullPayload",
    # Review Payloads
    "ReviewCreatedPayload",
    "ReviewReminderDayPayload",
    "ReviewReminderWeekPayload",
    "ReviewOthersCreatedPayload",
    # User Payloads
    "UserFollowedPayload",
    "UserFollowedUserCreatedPodPayload",
    # System Payloads
    "SystemSavedPodDeadlinePayload",
    "SystemSavedPodSpotOpenedPayload",
]
