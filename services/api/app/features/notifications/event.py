"""통합 알림 이벤트 정의"""

from enum import Enum

from .events.pod import PodEvent
from .events.review import ReviewEvent
from .events.system import SystemEvent
from .events.user import UserEvent


class NotificationEvent(str, Enum):
    """통합 알림 이벤트

    DB/API에는 이 enum의 value(문자열)가 저장됩니다.
    """

    # ============= Pod Events =============
    POD_JOIN_REQUESTED = PodEvent.JOIN_REQUESTED.value
    POD_JOIN_APPROVED = PodEvent.JOIN_APPROVED.value
    POD_JOIN_REJECTED = PodEvent.JOIN_REJECTED.value
    POD_MEMBER_JOINED = PodEvent.MEMBER_JOINED.value
    POD_UPDATED = PodEvent.UPDATED.value
    POD_CONFIRMED = PodEvent.CONFIRMED.value
    POD_CANCELED = PodEvent.CANCELED.value
    POD_STARTING_SOON = PodEvent.STARTING_SOON.value
    POD_LOW_ATTENDANCE = PodEvent.LOW_ATTENDANCE.value
    POD_CANCELED_SOON = PodEvent.CANCELED_SOON.value
    POD_COMPLETED = PodEvent.COMPLETED.value
    POD_LIKES_THRESHOLD = PodEvent.LIKES_THRESHOLD.value
    POD_VIEWS_THRESHOLD = PodEvent.VIEWS_THRESHOLD.value
    POD_CAPACITY_FULL = PodEvent.CAPACITY_FULL.value

    # ============= Review Events =============
    REVIEW_CREATED = ReviewEvent.CREATED.value
    REVIEW_REMINDER_DAY = ReviewEvent.REMINDER_DAY.value
    REVIEW_REMINDER_WEEK = ReviewEvent.REMINDER_WEEK.value
    REVIEW_OTHERS_CREATED = ReviewEvent.OTHERS_CREATED.value

    # ============= User Events =============
    USER_FOLLOWED = UserEvent.FOLLOWED.value
    USER_FOLLOWED_USER_CREATED_POD = UserEvent.FOLLOWED_USER_CREATED_POD.value

    # ============= System Events =============
    SYSTEM_SAVED_POD_DEADLINE = SystemEvent.SAVED_POD_DEADLINE.value
    SYSTEM_SAVED_POD_SPOT_OPENED = SystemEvent.SAVED_POD_SPOT_OPENED.value
