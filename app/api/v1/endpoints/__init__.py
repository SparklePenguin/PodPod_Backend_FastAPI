# endpoints 패키지 초기화
from .users import router as users_router
from .sessions import router as sessions_router
from .oauths import router as oauths_router
from .artists import router as artists_router

__all__ = [
    "users_router",
    "sessions_router",
    "oauths_router",
    "artists_router",
]
