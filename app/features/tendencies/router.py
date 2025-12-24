"""
Tendencies feature API endpoints
통합된 성향 테스트 관련 API 엔드포인트
"""

from fastapi import APIRouter

from .routers.survey_router import router as surveys_router

# 각 라우터 모듈에서 라우터 import
from .routers.tendency_router import router as tendencies_router

# 메인 라우터 생성
router = APIRouter()

# 각 라우터를 통합
router.include_router(tendencies_router, prefix="/tendencies", tags=["tendencies"])
router.include_router(surveys_router, prefix="/surveys", tags=["surveys"])
