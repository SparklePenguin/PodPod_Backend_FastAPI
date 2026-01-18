"""
예외 핸들러들 - FastAPI 앱에 등록되어 예외를 처리
"""

import logging
from typing import Union

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.schemas import BaseResponse

from .base import BusinessException
from .registry import get_error_info

logger = logging.getLogger(__name__)


def _get_error_key_from_http_exception(
    status_code: int, detail: str | None
) -> str | None:
    """
    HTTP 상태 코드와 detail 메시지로 errors.json의 에러 키 매핑

    Returns:
        errors.json에 정의된 에러 키 또는 None
    """
    detail_lower = (detail or "").lower()

    # 인증 관련 에러 (HTTPBearer 등에서 발생)
    if status_code == 403 and "not authenticated" in detail_lower:
        return "AUTHENTICATION_REQUIRED"
    if status_code == 401:
        if "expired" in detail_lower:
            return "TOKEN_EXPIRED"
        if "invalid" in detail_lower:
            return "INVALID_TOKEN"
        return "AUTHENTICATION_REQUIRED"

    # 일반 HTTP 상태 코드 매핑
    status_to_error_key = {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        500: "INTERNAL_SERVER_ERROR",
    }

    return status_to_error_key.get(status_code)


async def http_exception_handler(
    request: Request, exc: Union[HTTPException, StarletteHTTPException]
):
    """HTTPException 처리 → BaseResponse 패턴으로 응답"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    # HTTPException의 detail이 이미 BaseResponse 형태인지 확인
    if isinstance(exc.detail, dict) and "errorCode" in exc.detail:
        response = BaseResponse(
            data=None,
            error_key=exc.detail.get("error", "HTTP_ERROR"),
            error_code=exc.detail.get("errorCode"),
            http_status=exc.status_code,
            message_ko=exc.detail.get("messageKo", str(exc.detail)),
            message_en=exc.detail.get("messageEn", str(exc.detail)),
            dev_note=exc.detail.get("devNote", "HTTP error occurred"),
        )
        return JSONResponse(
            status_code=exc.status_code, content=response.model_dump(by_alias=True)
        )

    # errors.json에서 매핑된 에러 키 찾기
    error_key = _get_error_key_from_http_exception(
        exc.status_code, str(exc.detail) if exc.detail else None
    )

    if error_key:
        try:
            error_info = get_error_info(error_key)
            response = BaseResponse(
                data=None,
                error_key=error_key,
                error_code=error_info.code,
                http_status=error_info.http_status,
                message_ko=error_info.message_ko,
                message_en=error_info.message_en,
                dev_note=error_info.dev_note,
            )
            return JSONResponse(
                status_code=error_info.http_status,
                content=response.model_dump(by_alias=True),
            )
        except ValueError:
            # errors.json에 해당 키가 없으면 기본 처리로 폴백
            pass

    # 매핑되지 않은 HTTPException은 기본 형태로 변환
    response = BaseResponse(
        data=None,
        error_key="HTTP_ERROR",
        error_code=exc.status_code,
        http_status=exc.status_code,
        message_ko=str(exc.detail),
        message_en=str(exc.detail),
        dev_note="HTTP error occurred",
    )

    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


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
        error_key="REQUEST_VALIDATION_ERROR",
        error_code=4220,
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message_ko=message,
        message_en="Request validation failed",
        dev_note="Request validation failed",
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(by_alias=True),
    )


async def value_error_handler(request: Request, exc: ValueError):
    """ValueError 처리 → 400 Bad Request"""
    logger.error(f"Value Error: {str(exc)}")
    response = BaseResponse(
        data=None,
        error_key="VALIDATION_ERROR",
        error_code=4000,
        http_status=status.HTTP_400_BAD_REQUEST,
        message_ko=str(exc),
        message_en=str(exc),
        dev_note="Request validation failed",
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump(by_alias=True),
    )


async def business_exception_handler(request: Request, exc: Exception):
    """BusinessException 처리 → BaseResponse 패턴으로 응답"""
    # 타입 체크를 통해 BusinessException인지 확인
    if not isinstance(exc, BusinessException):
        # BusinessException이 아닌 경우 일반 예외 핸들러로 위임
        return await general_exception_handler(request, exc)

    logger.warning(f"Business Exception: {exc.error_code} - {exc.message_ko}")

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=4090,  # 중복 제안 에러 코드
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def general_exception_handler(request: Request, exc: Exception):
    """예상치 못한 일반적인 예외 → 500 Internal Server Error"""
    import traceback

    # 요청 본문 읽기
    request_body = None
    try:
        if hasattr(request, "_body") and request._body:
            request_body = request._body.decode("utf-8")
        elif request.method in ["POST", "PUT", "PATCH"]:
            # 미들웨어에서 이미 읽었을 수 있지만, 다시 시도
            body = await request.body()
            if body:
                request_body = body.decode("utf-8")
    except Exception as e:
        request_body = f"Failed to read request body: {str(e)}"

    # 상세한 에러 정보 로깅
    error_details = {
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "traceback": traceback.format_exc(),
        "request_url": str(request.url),
        "request_method": request.method,
        "request_headers": dict(request.headers),
        "request_body": request_body,
        "query_params": str(request.query_params),
        "client_ip": request.client.host if request.client else None,
    }

    logger.error(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)}", extra=error_details
    )

    # 개발 환경에서는 더 자세한 정보 제공
    dev_note = f"Exception: {type(exc).__name__}: {str(exc)}"
    if hasattr(exc, "__traceback__"):
        import traceback

        dev_note += f"\nTraceback: {traceback.format_exc()}"

    response = BaseResponse(
        data=None,
        error_key="INTERNAL_SERVER_ERROR",
        error_code=5001,
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message_ko="서버 내부 오류가 발생했습니다.",
        message_en="Internal server error occurred.",
        dev_note=dev_note,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(by_alias=True),
    )
