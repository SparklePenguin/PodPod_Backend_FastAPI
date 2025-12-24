"""
Auth feature API endpoints
통합된 인증 관련 API 엔드포인트
"""
from fastapi import APIRouter

# 각 라우터 모듈에서 라우터 import
from .routers.session_router import router as sessions_router
from .routers.oauth_router import router as oauths_router

# 메인 라우터 생성
router = APIRouter()

# 각 라우터를 통합
router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
router.include_router(oauths_router, prefix="/oauths", tags=["oauths"])
