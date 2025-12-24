"""
Artists feature API endpoints
통합된 아티스트 관련 API 엔드포인트
"""

from fastapi import APIRouter

# 각 라우터 모듈에서 라우터 import
from .routers.artist_router import router as artists_router
from .routers.schedule_router import router as schedules_router
from .routers.suggestion_router import router as suggestions_router

# 메인 라우터 생성
router = APIRouter()

# 각 라우터를 통합
router.include_router(artists_router, prefix="/artists", tags=["artists"])
router.include_router(
    schedules_router, prefix="/artist/schedules", tags=["artist-schedules"]
)
router.include_router(suggestions_router, prefix="/artist-suggestions")
