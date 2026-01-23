"""
API v1 Router
모든 feature router를 통합하는 메인 라우터
"""
from itertools import chain

from fastapi import APIRouter

# Artists routers
from app.features.artists.routers.artist_router import router as artists_router
from app.features.artists.routers.artist_schedule_router import (
    router as schedules_router,
)
from app.features.artists.routers.artist_suggestion_router import (
    router as suggestions_router,
)
from app.features.chat.routers.chat_router import router as chat_router
# Chat routers
from app.features.chat.routers.websocket_router import router as chat_websocket_router
# Follow router
from app.features.follow.routers.follow_router import router as follow_router
# Locations router
from app.features.locations.routers.location_router import router as locations_router
# Notifications router
from app.features.notifications.routers.notification_router import (
    router as notifications_router,
)
# Auth routers
from app.features.oauth.routers import (
    KaKoOauthController,
    GoogleOauthController,
    AppleOauthController
)
# from app.features.oauth.routers.oauth_router import router as oauths_router
# Pods routers
from app.features.pods.routers.application_router import (
    applications_router,
    pod_applications_router,
)
from app.features.pods.routers.like_router import router as pod_likes_router
from app.features.pods.routers.pod_router import router as pods_router
from app.features.pods.routers.review_router import (
    pod_reviews_router,
    reviews_router,
)
# Reports router
from app.features.reports.routers.report_router import router as reports_router
# Session APIS
from app.features.session.routers import SessionController
# System routers
from app.features.system.routers.health import router as health_router
# Tendencies routers
from app.features.tendencies.routers.survey_router import router as surveys_router
from app.features.tendencies.routers.tendency_router import router as tendencies_router
# Users Apis
from app.features.users.routers import (
    UserCommonController,
    UserController,
    UserPreferredArtistsController,
    BlockUserController,
    UserFollowingsController,
    UserNotificationController,
    ProfileImageRouter,
)

# 메인 API 라우터 생성
# 구체적인 경로를 먼저 등록해야 함 (FastAPI는 등록 순서대로 매칭)
api_router = APIRouter()

for router in chain.from_iterable([
    # 인증 관련 라우터 (features/auth)
    [
        SessionController.ROUTER
    ],

    # 인증 관련 라우터 (features/auth)
    [
        KaKoOauthController.ROUTER,
        GoogleOauthController.ROUTER,
        AppleOauthController.ROUTER
    ],

    # 사용자 관련 라우터 (features/users)
    [
        UserCommonController.ROUTER,
        UserController.ROUTER,
        UserPreferredArtistsController.ROUTER,
        UserFollowingsController.ROUTER,
        BlockUserController.ROUTER,
        UserNotificationController.ROUTER,

        ProfileImageRouter.router  # 랜덤 프로필 이미지 라우터 (users)
    ],

    # 아티스트 관련 라우터 (features/artists)
    [artists_router, schedules_router, suggestions_router],

    # 성향 테스트 관련 라우터 (features/tendencies)
    [tendencies_router, surveys_router],

    # 파티 관련 라우터 (features/pods)
    [
        pods_router, pod_likes_router, pod_applications_router,
        applications_router, pod_reviews_router, reviews_router
    ],

    # 팔로우 관련 라우터 (features/follow)
    [follow_router],

    # 알림 관련 라우터 (features/notifications)
    [notifications_router],

    # 지역 관련 라우터 (features/locations)
    [locations_router],

    # 신고 관련 라우터 (features/reports)
    [reports_router],

    # 채팅 라우터 (chat)
    [chat_router, chat_websocket_router],

    # 시스템 관련 라우터 (system)
    [health_router]
]):
    api_router.include_router(router)
