"""
Notifications feature API endpoints
통합된 알림 관련 API 엔드포인트
"""
from fastapi import APIRouter

from .routers.notification_router import router as notification_router

router = APIRouter()
router.include_router(notification_router)
