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
        response = BaseResponse(
            data=None,
            error=exc.detail.get("error_code", "HTTP_ERROR"),
            error_code=exc.detail["code"],
            http_status=exc.status_code,
            message_ko=exc.detail["message"],
            message_en=exc.detail["message"],
            devNote=exc.detail.get("devNote", "HTTP error occurred"),
        )
    else:
        # 일반적인 HTTPException의 경우 BaseResponse 형태로 변환
        response = BaseResponse(
            data=None,
            error="HTTP_ERROR",
            error_code=exc.status_code,
            http_status=exc.status_code,
            message_ko=str(exc.detail),
            message_en=str(exc.detail),
            devNote="HTTP error occurred",
        )

    return JSONResponse(status_code=exc.status_code, content=response.model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """클라이언트 요청 데이터 검증 실패 → 422 Unprocessable Entity"""
    logger.error(f"Request Validation Error: {exc.errors()}")

    # 더 명확한 오류 메시지 생성
    error_messages = []
    for error in exc.errors():
        if error["type"] == "missing":
            field_name = error["loc"][-1] if error["loc"] else "unknown"
            error_messages.append(f"{field_name} 필드가 필요합니다")
        elif error["type"] == "value_error":
            # form parser에서 생성한 명확한 메시지 사용
            if "필수 필드가 누락되었습니다" in error["msg"]:
                error_messages.append(error["msg"])
            else:
                error_messages.append(
                    f"데이터 형식이 올바르지 않습니다: {error['msg']}"
                )
        else:
            error_messages.append(error["msg"])

    # 중복 제거하고 하나의 메시지로 합치기
    unique_messages = list(set(error_messages))
    if len(unique_messages) == 1:
        message = unique_messages[0]
    else:
        message = f"요청 데이터에 문제가 있습니다: {'; '.join(unique_messages)}"

    response = BaseResponse(
        data=None,
        error="REQUEST_VALIDATION_ERROR",
        error_code=4220,
        http_status=HttpStatus.UNPROCESSABLE_ENTITY,
        message_ko=message,
        message_en="Request validation failed",
        devNote="Request validation failed",
    )
    return JSONResponse(
        status_code=HttpStatus.UNPROCESSABLE_ENTITY, content=response.model_dump()
    )


async def value_error_handler(request: Request, exc: ValueError):
    """ValueError 처리 → 400 Bad Request"""
    logger.error(f"Value Error: {str(exc)}")
    response = BaseResponse(
        data=None,
        error="VALIDATION_ERROR",
        error_code=4000,
        http_status=HttpStatus.BAD_REQUEST,
        message_ko=str(exc),
        message_en=str(exc),
        devNote="Request validation failed",
    )
    return JSONResponse(
        status_code=HttpStatus.BAD_REQUEST, content=response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """예상치 못한 일반적인 예외 → 500 Internal Server Error"""
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}")
    response = BaseResponse(
        data=None,
        error="INTERNAL_SERVER_ERROR",
        error_code=5001,
        http_status=HttpStatus.INTERNAL_SERVER_ERROR,
        message_ko="서버 내부 오류가 발생했습니다.",
        message_en="Internal server error occurred.",
        devNote="Unhandled server error",
    )
    return JSONResponse(
        status_code=HttpStatus.INTERNAL_SERVER_ERROR, content=response.model_dump()
    )
