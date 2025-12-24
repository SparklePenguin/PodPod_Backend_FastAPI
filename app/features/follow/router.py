"""
Follow feature API endpoints
통합된 팔로우 관련 API 엔드포인트
"""
from fastapi import APIRouter

from .routers.follow_router import router as follow_router

router = APIRouter()
router.include_router(follow_router)
