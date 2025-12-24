import logging
from typing import Union

from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.schemas import BaseResponse
from app.core.http_status import HttpStatus

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """비즈니스 로직 예외"""

    def __init__(
        self,
        error_code: str,
        message_ko: str,
        message_en: str | None = None,
        status_code: int = 400,
        dev_note: str | None = None,
    ):
        self.error_code = error_code
        self.message_ko = message_ko
        self.message_en = message_en or message_ko
        self.status_code = status_code
        self.dev_note = dev_note or "Business logic error"
        super().__init__(self.message_ko)


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
    else:
        # 일반적인 HTTPException의 경우 BaseResponse 형태로 변환
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
        http_status=HttpStatus.UNPROCESSABLE_ENTITY,
        message_ko=message,
        message_en="Request validation failed",
        dev_note="Request validation failed",
    )
    return JSONResponse(
        status_code=HttpStatus.UNPROCESSABLE_ENTITY,
        content=response.model_dump(by_alias=True),
    )


async def value_error_handler(request: Request, exc: ValueError):
    """ValueError 처리 → 400 Bad Request"""
    logger.error(f"Value Error: {str(exc)}")
    response = BaseResponse(
        data=None,
        error_key="VALIDATION_ERROR",
        error_code=4000,
        http_status=HttpStatus.BAD_REQUEST,
        message_ko=str(exc),
        message_en=str(exc),
        dev_note="Request validation failed",
    )
    return JSONResponse(
        status_code=HttpStatus.BAD_REQUEST, content=response.model_dump(by_alias=True)
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
        http_status=HttpStatus.INTERNAL_SERVER_ERROR,
        message_ko="서버 내부 오류가 발생했습니다.",
        message_en="Internal server error occurred.",
        dev_note=dev_note,
    )
    return JSONResponse(
        status_code=HttpStatus.INTERNAL_SERVER_ERROR,
        content=response.model_dump(by_alias=True),
    )
