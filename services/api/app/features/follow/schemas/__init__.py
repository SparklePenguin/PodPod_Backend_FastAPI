"""Follow feature schemas"""

from app.features.users.schemas.user_dto import UserDto

from .follow_schemas import (
    FollowInfoDto,
    FollowNotificationStatusDto,
    FollowNotificationUpdateRequest,
    FollowRequest,
    FollowStatsDto,
)

__all__ = [
    "FollowInfoDto",
    "FollowStatsDto",
    "FollowRequest",
    "FollowNotificationStatusDto",
    "FollowNotificationUpdateRequest",
    "UserDto",
]
