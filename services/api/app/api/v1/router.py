"""
API v1 Router
모든 feature router를 통합하는 메인 라우터
"""

# Admin routers
from app.features.admin.routers.error_codes import router as error_codes_router
from app.features.admin.routers.fcm import router as fcm_router
from app.features.admin.routers.sendbird import router as sendbird_router

# Artists routers
from app.features.artists.routers.artist_router import router as artists_router
from app.features.artists.routers.artist_schedule_router import (
    router as schedules_router,
)
from app.features.artists.routers.artist_suggestion_router import (
    router as suggestions_router,
)

# Chat routers
from app.features.chat.routers.websocket_router import router as chat_websocket_router
from app.features.chat.routers.chat_router import router as chat_router

# Follow router
from app.features.follow.routers.follow_router import router as follow_router

# Locations router
from app.features.locations.routers.location_router import router as locations_router

# Notifications router
from app.features.notifications.routers.notification_router import (
    router as notifications_router,
)

# Auth routers
from app.features.oauth.routers.oauth_router import router as oauths_router

# Pods routers
from app.features.pods.routers.like_router import router as pod_likes_router
from app.features.pods.routers.pod_router import router as pods_router
from app.features.pods.routers.recruitment_router import router as recruitments_router
from app.features.pods.routers.review_router import router as pod_reviews_router

# Reports router
from app.features.reports.routers.report_router import router as reports_router

# Session router
from app.features.session.routers.session_router import router as sessions_router

# System routers
from app.features.system.routers.health import router as health_router

# Tendencies routers
from app.features.tendencies.routers.survey_router import router as surveys_router
from app.features.tendencies.routers.tendency_router import router as tendencies_router
from app.features.users.routers.profile_image_router import (
    router as profile_images_router,
)

# Users routers
from app.features.users.routers.block_user_router import (
    router as block_user_router,
)
from app.features.users.routers.user_notification_router import (
    router as user_notification_router,
)
from app.features.users.routers.user_router import router as users_router

from fastapi import APIRouter

# 메인 API 라우터 생성
api_router = APIRouter()

# 사용자 관련 라우터 (features/users)
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(
    block_user_router, prefix="/users/blocks", tags=["users"]
)
api_router.include_router(
    user_notification_router,
    prefix="/users/notification-settings",
    tags=["users"],
)

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
api_router.include_router(
    pod_reviews_router, prefix="/pod-reviews", tags=["pod-reviews"]
)

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

# 랜덤 프로필 이미지 라우터 (users)
api_router.include_router(
    profile_images_router, prefix="/profile-images", tags=["profile-images"]
)

# 채팅 라우터 (chat)
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])

# 시스템 관련 라우터 (system)
api_router.include_router(health_router, tags=["health"])

# 관리자 관련 라우터 (admin)
api_router.include_router(error_codes_router, prefix="/admin", tags=["admin"])
api_router.include_router(fcm_router, prefix="/admin", tags=["admin"])
api_router.include_router(sendbird_router, prefix="/admin/sendbird", tags=["admin"])

# 채팅 WebSocket 라우터 (chat)
api_router.include_router(chat_websocket_router, prefix="/chat", tags=["chat"])
