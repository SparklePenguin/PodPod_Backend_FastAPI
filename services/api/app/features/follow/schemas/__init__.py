"""Follow feature schemas"""

from .follow_info_dto import FollowInfoDto
from .follow_notification_status_dto import FollowNotificationStatusDto
from .follow_notification_update_request import FollowNotificationUpdateRequest
from .follow_request import FollowRequest
from .follow_stats_dto import FollowStatsDto
# UserDto는 이제 users 도메인으로 이동했습니다.
# 하위 호환성을 위해 import만 유지합니다.
from app.features.users.schemas.user_dto import UserDto

__all__ = [
    "FollowNotificationStatusDto",
    "FollowNotificationUpdateRequest",
    "FollowRequest",
    "FollowInfoDto",
    "FollowStatsDto",
    "UserDto",
]
