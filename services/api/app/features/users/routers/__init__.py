"""
Users routers
"""

from app.features.users.routers._base import (
    UserRouterRootLabel,
    UserPreferredArtistsRouterLabel
)
from .block_user_router import (
    BlockUserRouter
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
    UserCommonRouter,
    UserUpdateRouter,
    UserDeleteRouter,
    UserRegistRouter,
    UserSearchRouter
)
from .profile_image_router import (
    ProfileImageRouter
)

# from app.features.users.routers.profile_image_router import (
#     router as profile_image_router,
# )
# from app.features.users.routers.user_router import router as user_router
#
# from .user_preferred_artist_router import UserPreferredArtistsRouter
