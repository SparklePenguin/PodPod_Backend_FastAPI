from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas.common import BaseResponse
from app.core.http_status import HttpStatus
import logging

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException 처리 → BaseResponse 패턴으로 응답"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    # HTTPException의 detail이 이미 BaseResponse 형태인지 확인
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        response = BaseResponse.error(
            code=HttpStatus(exc.status_code),
            message=exc.detail["message"],
        )
    else:
        # 일반적인 HTTPException의 경우 BaseResponse 형태로 변환
        response = BaseResponse.error(
            code=HttpStatus(exc.status_code),
            message=str(exc.detail),
        )

    return JSONResponse(status_code=exc.status_code, content=response.model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """클라이언트 요청 데이터 검증 실패 → 422 Unprocessable Entity"""
    logger.error(f"Request Validation Error: {exc.errors()}")
    response = BaseResponse.error(
        code=HttpStatus.UNPROCESSABLE_ENTITY,
        message="요청 데이터 검증에 실패했습니다.",
    )
    return JSONResponse(
        status_code=HttpStatus.UNPROCESSABLE_ENTITY, content=response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """예상치 못한 일반적인 예외 → 500 Internal Server Error"""
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}")
    response = BaseResponse.error(
        code=HttpStatus.INTERNAL_SERVER_ERROR,
        message="서버 내부 오류가 발생했습니다.",
    )
    return JSONResponse(
        status_code=HttpStatus.INTERNAL_SERVER_ERROR, content=response.model_dump()
    )
