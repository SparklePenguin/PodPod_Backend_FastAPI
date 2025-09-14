"""
관리자용 엔드포인트
"""

from fastapi import APIRouter
from .error_codes import router as error_codes_router

router = APIRouter(tags=["admin"])

# 에러 코드 관리 라우터 추가
router.include_router(error_codes_router)
