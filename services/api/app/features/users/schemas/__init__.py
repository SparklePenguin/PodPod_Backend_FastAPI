"""Users feature schemas"""

from .user_block_schemas import (
    BlockedUserDto,
    BlockInfoDto,
)
from .user_notification_schemas import (
    UpdateUserNotificationSettingsRequest,
    UserNotificationSettingsDto,
)
from .user_schemas import (
    AcceptTermsRequest,
    RandomProfileImageDto,
    UpdatePreferredArtistsRequest,
    UpdateProfileRequest,
    UpdateUserRequest,
    UserDetailDto,
    UserDto,
)

__all__ = [
    # User 기본
    "UserDto",
    "UserDetailDto",
    "UpdateUserRequest",
    "UpdateProfileRequest",
    "AcceptTermsRequest",
    "UpdatePreferredArtistsRequest",
    "RandomProfileImageDto",
    # User Notification
    "UserNotificationSettingsDto",
    "UpdateUserNotificationSettingsRequest",
    # User Block
    "BlockedUserDto",
    "BlockInfoDto",
]
