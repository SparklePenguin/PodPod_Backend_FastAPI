"""
Users routers
"""

from app.features.users.routers._base import (
    UserRouterRootLabel,
    UserPreferredArtistsRouterLabel,
UserCommonRouterLabel, UserNotificationRouterLabel, \
    UserFollowingsRouterLabel, BlockUserRouterLabel
)
from .block_user_router import (
    BlockUserRouter
)
from .profile_image_router import (
    ProfileImageRouter
)
from .user_commons_router import (
    UserCommonRouter
)
from .user_followings_router import (
    UserFollowingsRouter
)
from .user_notification_router import (
    UserNotificationRouter
)
from .user_preferred_artist_router import (
    UserPreferredArtistsRouter
)
from .user_router import (
    UserFcmTokenUpdateRouter,
    UserRetreiveRouter,
    UserBaseRouter,
    UserTermsAgreementRouter
)
