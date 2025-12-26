"""
API v1 Router
모든 feature router를 통합하는 메인 라우터
"""

from fastapi import APIRouter

# Artists routers
from app.features.artists.routers.artist_router import router as artists_router
from app.features.artists.routers.artist_schedule_router import router as schedules_router
from app.features.artists.routers.artist_suggestion_router import router as suggestions_router

# Auth routers
from app.features.auth.routers.session_router import router as sessions_router
from app.features.auth.routers.oauth_router import router as oauths_router

# Follow router
from app.features.follow.routers.follow_router import router as follow_router

# Locations router
from app.features.locations.routers.location_router import router as locations_router

# Notifications router
from app.features.notifications.routers.notification_router import router as notifications_router

# Pods routers
from app.features.pods.routers.like_router import router as pod_likes_router
from app.features.pods.routers.pod_router import router as pods_router
from app.features.pods.routers.recruitment_router import router as recruitments_router
from app.features.pods.routers.review_router import router as pod_reviews_router

# Reports router
from app.features.reports.routers.report_router import router as reports_router

# Tendencies routers
from app.features.tendencies.routers.survey_router import router as surveys_router
from app.features.tendencies.routers.tendency_router import router as tendencies_router

# Users router (routers 폴더 없음, router.py에 직접 정의)
from app.features.users.router import router as users_router

from .endpoints import (
    health,
    random_profile_images,
    webhooks,
)
from .endpoints.admin import router as admin_router

# 메인 API 라우터 생성
api_router = APIRouter()

# 사용자 관련 라우터 (features/users)
api_router.include_router(users_router, prefix="/users", tags=["users"])

# 인증 관련 라우터 (features/auth)
api_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
api_router.include_router(oauths_router, prefix="/oauths", tags=["oauths"])

# 아티스트 관련 라우터 (features/artists)
api_router.include_router(artists_router, prefix="/artists", tags=["artists"])
api_router.include_router(
    schedules_router, prefix="/artist/schedules", tags=["artist-schedules"]
)
api_router.include_router(suggestions_router, prefix="/artist-suggestions")

# 성향 테스트 관련 라우터 (features/tendencies)
api_router.include_router(tendencies_router, prefix="/tendencies", tags=["tendencies"])
api_router.include_router(surveys_router, prefix="/surveys", tags=["surveys"])

# 파티 관련 라우터 (features/pods)
api_router.include_router(pods_router, prefix="/pods", tags=["pods"])
api_router.include_router(pod_likes_router, prefix="/pods", tags=["pods"])
api_router.include_router(recruitments_router, prefix="/pods", tags=["pods"])
api_router.include_router(pod_reviews_router, prefix="/pod-reviews", tags=["pod-reviews"])

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
