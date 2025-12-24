"""
Locations feature API endpoints
통합된 지역 관련 API 엔드포인트
"""
from fastapi import APIRouter

from .routers.location_router import router as location_router

router = APIRouter()
router.include_router(location_router)
