# endpoints 패키지 초기화
from .users import router as users_router
from .sessions import router as sessions_router
from .oauths import router as oauths_router
from .artists import router as artists_router
from .tendencies import router as tendencies_router
from .surveys import router as surveys_router
from .artist_schedules import router as artist_schedules_router
from .follow import router as follow_router
from .artist_suggestions import router as artist_suggestions_router
from .pod_reviews import router as pod_reviews_router
from .locations import router as locations_router
from .reports import router as reports_router
from .health import router as health_router
from .notifications import router as notifications_router
from .user_notification_settings import router as user_notification_settings_router
from .random_profile_images import router as random_profile_images_router

__all__ = [
    "users_router",
    "sessions_router",
    "oauths_router",
    "artists_router",
    "tendencies_router",
    "surveys_router",
    "artist_schedules_router",
    "follow_router",
    "artist_suggestions_router",
    "pod_reviews_router",
    "locations_router",
    "reports_router",
    "health_router",
    "notifications_router",
    "user_notification_settings_router",
    "random_profile_images_router",
]
