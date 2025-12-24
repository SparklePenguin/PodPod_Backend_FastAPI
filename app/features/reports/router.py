"""
Reports feature API endpoints
통합된 신고 관련 API 엔드포인트
"""

from fastapi import APIRouter

from .routers.report_router import router as report_router

router = APIRouter()
router.include_router(report_router)
