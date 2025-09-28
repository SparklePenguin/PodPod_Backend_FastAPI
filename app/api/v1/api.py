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
    artist_schedules.router, prefix="/artist/schedules", tags=["artistSchedule"]
)

# 성향 테스트 관련 라우터
api_router.include_router(tendencies.router, prefix="/tendencies", tags=["tendencies"])

# 설문 관련 라우터
api_router.include_router(surveys.router, prefix="/surveys", tags=["surveys"])


# 파티 관련 라우터
api_router.include_router(pods.router, prefix="/pods", tags=["pods"])
api_router.include_router(recruitments, prefix="/recruitments", tags=["recruitments"])
api_router.include_router(pod_likes, prefix="/pods", tags=["podLikes"])

# 팔로우 관련 라우터
api_router.include_router(follow.router, prefix="/follow", tags=["follow"])

# 관리자 관련 라우터
api_router.include_router(admin_router)
