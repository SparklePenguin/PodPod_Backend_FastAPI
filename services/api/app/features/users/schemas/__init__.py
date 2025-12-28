"""Users feature schemas"""

from .random_profile_image import RandomProfileImageResponse
from .user_block import BlockedUserDto, BlockUserResponse
from .user_dto import UserDto, UserDtoInternal
from .user_notification import (
    UpdateUserNotificationSettingsRequest,
    UserNotificationSettingsDto,
)
from .user_request import (
    AcceptTermsRequest,
    UpdatePreferredArtistsRequest,
    UpdateProfileRequest,
    UpdateUserRequest,
)

__all__ = [
    "AcceptTermsRequest",
    "BlockedUserDto",
    "BlockUserResponse",
    "RandomProfileImageResponse",
    "UpdatePreferredArtistsRequest",
    "UpdateProfileRequest",
    "UpdateUserNotificationSettingsRequest",
    "UpdateUserRequest",
    "UserDto",
    "UserDtoInternal",
    "UserNotificationSettingsDto",
]
