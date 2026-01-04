"""
모든 SQLAlchemy 모델을 한 곳에서 import하는 모듈
Alembic 마이그레이션에서 사용
"""

# Artists
from app.features.artists.models import (
    Artist,
    ArtistImage,
    ArtistName,
    ArtistUnit,
)

# Chat
from app.features.chat.models import (
    ChatMember,
    ChatMessage,
    ChatRoom,
)

# Follow
from app.features.follow.models import Follow

# Locations
from app.features.locations.models import Location

# Notifications
from app.features.notifications.models import Notification

# Pods
from app.features.pods.models import (
    Application,
    Pod,
    PodDetail,
    PodImage,
    PodLike,
    PodMember,
    PodRating,
    PodReview,
    PodView,
)

# Tendencies
from app.features.tendencies.models import (
    TendencyResult,
    TendencySurvey,
    UserTendencyResult,
)

# Users
from app.features.users.models import (
    PreferredArtist,
    User,
    UserBlock,
    UserNotificationSettings,
    UserReport,
)

__all__ = [
    # Artists
    "Artist",
    "ArtistImage",
    "ArtistName",
    "ArtistUnit",
    # Follow
    "Follow",
    # Locations
    "Location",
    # Notifications
    "Notification",
    # Chat
    "ChatMember",
    "ChatMessage",
    "ChatRoom",
    # Pods
    "Application",
    "Pod",
    "PodDetail",
    "PodImage",
    "PodLike",
    "PodMember",
    "PodRating",
    "PodReview",
    "PodView",
    # Tendencies
    "TendencyResult",
    "TendencySurvey",
    "UserTendencyResult",
    # Users
    "PreferredArtist",
    "User",
    "UserBlock",
    "UserNotificationSettings",
    "UserReport",
]
