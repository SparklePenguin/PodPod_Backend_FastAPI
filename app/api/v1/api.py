from fastapi import APIRouter

from app.features.artists.router import router as artists_router
from app.features.auth.router import router as auth_router
from app.features.follow.router import router as follow_router
from app.features.locations.router import router as locations_router
from app.features.notifications.router import router as notifications_router
from app.features.pods.router import router as pods_router
from app.features.reports.router import router as reports_router
from app.features.tendencies.router import router as tendencies_router
from app.features.users.router import router as users_router

from .endpoints import (
    health,
    random_profile_images,
    webhooks,
)
from .endpoints.admin import router as admin_router

api_router = APIRouter()

# 사용자 관련 라우터 (features/users)
api_router.include_router(users_router, prefix="/users", tags=["users"])

# 인증 관련 라우터 (features/auth)
api_router.include_router(auth_router)

# 아티스트 관련 라우터 (features/artists)
api_router.include_router(artists_router)

# 성향 테스트 관련 라우터 (features/tendencies)
api_router.include_router(tendencies_router)

# 파티 관련 라우터 (features/pods) - 이미 prefix가 포함되어 있음
api_router.include_router(pods_router)

# 팔로우 관련 라우터 (features/follow)
api_router.include_router(follow_router, prefix="/follow", tags=["follow"])

# 알림 관련 라우터 (features/notifications)
api_router.include_router(
    notifications_router, prefix="/notifications", tags=["notifications"]
)

# 지역 관련 라우터 (features/locations)
api_router.include_router(locations_router, prefix="/regions", tags=["regions"])

# 신고 관련 라우터 (features/reports)
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])

# 관리자 관련 라우터
api_router.include_router(admin_router)

# 헬스 체크 라우터
api_router.include_router(health.router, tags=["health"])

# 랜덤 프로필 이미지 라우터
api_router.include_router(
    random_profile_images.router, prefix="/profile-images", tags=["profile-images"]
)

# 웹훅 라우터
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
