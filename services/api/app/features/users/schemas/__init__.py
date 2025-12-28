"""Users feature schemas"""

from .accept_terms_request import AcceptTermsRequest
from .block_user_response import BlockUserResponse
from .blocked_user_dto import BlockedUserDto
from .random_profile_image import RandomProfileImageDto
from .update_user_notification_settings_request import (
    UpdateUserNotificationSettingsRequest,
)
from .user_detail_dto import UserDetailDto
from .user_dto import UserDto
from .user_notification_settings_dto import UserNotificationSettingsDto
from .update_preferred_artists_request import UpdatePreferredArtistsRequest
from .update_profile_request import UpdateProfileRequest
from .update_user_request import UpdateUserRequest

__all__ = [
    "AcceptTermsRequest",
    "BlockedUserDto",
    "BlockUserResponse",
    "RandomProfileImageDto",
    "UpdatePreferredArtistsRequest",
    "UpdateProfileRequest",
    "UpdateUserNotificationSettingsRequest",
    "UpdateUserRequest",
    "UserDetailDto",
    "UserDto",
    "UserNotificationSettingsDto",
]
