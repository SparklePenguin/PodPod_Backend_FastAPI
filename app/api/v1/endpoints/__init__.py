# endpoints 패키지 초기화
# 현재 사용 중인 엔드포인트만 import
from .health import router as health_router
from .random_profile_images import router as random_profile_images_router

__all__ = [
    "health_router",
    "random_profile_images_router",
]
