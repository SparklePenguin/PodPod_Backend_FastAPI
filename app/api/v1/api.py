from fastapi import APIRouter
from .endpoints import (
    users,
    sessions,
    oauths,
    artists,
    tendencies,
    surveys,
    artist_schedules,
    follow,
    artist_suggestions,
    pod_reviews,
    locations,
    reports,
    health,
    notifications,
    notification_settings,
)
from .endpoints.pod import pods, recruitments, pod_likes
from .endpoints.admin import router as admin_router

api_router = APIRouter()

# 사용자 관련 라우터
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 세션 관련 라우터
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

# OAuth 관련 라우터
api_router.include_router(oauths.router, prefix="/oauths", tags=["oauths"])

# 아티스트 관련 라우터
api_router.include_router(artists.router, prefix="/artists", tags=["artists"])
api_router.include_router(
    artist_schedules.router, prefix="/artist/schedules", tags=["artist-schedules"]
)
api_router.include_router(artist_suggestions.router, prefix="/artist-suggestions")

# 성향 테스트 관련 라우터
api_router.include_router(tendencies.router, prefix="/tendencies", tags=["tendencies"])

# 설문 관련 라우터
api_router.include_router(surveys.router, prefix="/surveys", tags=["surveys"])


# 파티 관련 라우터
api_router.include_router(pods.router, prefix="/pods", tags=["pods"])
api_router.include_router(recruitments, prefix="/recruitments", tags=["recruitments"])
api_router.include_router(pod_likes, prefix="/pod-likes", tags=["podLikes"])

# 팔로우 관련 라우터
api_router.include_router(follow.router, prefix="/follow", tags=["follow"])

# 알림 관련 라우터
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(
    notification_settings.router, prefix="/notification-settings", tags=["notification-settings"]
)

# 후기 관련 라우터
api_router.include_router(pod_reviews.router, prefix="/reviews", tags=["reviews"])

# 지역 관련 라우터
api_router.include_router(locations.router, prefix="/regions", tags=["regions"])

# 신고 관련 라우터
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

# 관리자 관련 라우터
api_router.include_router(admin_router)

# 헬스 체크 라우터
api_router.include_router(health.router, tags=["health"])
