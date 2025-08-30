from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """클라이언트 요청 데이터 검증 실패 → 422 Unprocessable Entity"""
    logger.error(f"Request Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "validation_error",
            "status": 422,
            "message": "요청 데이터 검증에 실패했습니다.",
        },
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """서버 내부 Pydantic 모델 검증 실패 → 500 Internal Server Error"""
    logger.error(f"Pydantic Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "validation_error",
            "status": 500,
            "message": "서버 내부 데이터 검증 오류가 발생했습니다.",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """예상치 못한 일반적인 예외 → 500 Internal Server Error"""
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "internal_server_error",
            "status": 500,
            "message": "서버 내부 오류가 발생했습니다.",
        },
    )
