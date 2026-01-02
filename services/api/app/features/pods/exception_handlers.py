"""
Pods 도메인 전용 Exception Handler

이 모듈은 Pods 도메인의 예외를 처리하는 핸들러를 정의합니다.
각 핸들러는 BaseResponse 패턴으로 일관된 응답을 반환합니다.

중요: 이 파일은 반드시 EXCEPTION_HANDLERS 딕셔너리를 export해야 합니다.
     이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
"""


from app.common.schemas import BaseResponse
from app.features.pods.exceptions import (
    AlreadyAppliedException,
    AlreadyMemberException,
    InvalidImageException,
    NoPodAccessPermissionException,
    PodAccessDeniedException,
    PodAlreadyClosedException,
    PodIsFullException,
    PodNotFoundException,
    ReviewAlreadyExistsException,
    ReviewNotFoundException,
    ReviewPermissionDeniedException,
)
from fastapi import Request
from fastapi.responses import JSONResponse



async def pod_not_found_handler(request: Request, exc: PodNotFoundException):
    """PodNotFoundException 처리: 파티를 찾을 수 없는 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def no_pod_access_permission_handler(
    request: Request, exc: NoPodAccessPermissionException
):
    """NoPodAccessPermissionException 처리: 파티 접근 권한이 없는 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def pod_already_closed_handler(request: Request, exc: PodAlreadyClosedException):
    """PodAlreadyClosedException 처리: 이미 처리된 파티인 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def pod_is_full_handler(request: Request, exc: PodIsFullException):
    """PodIsFullException 처리: 파티가 가득 찬 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def already_member_handler(request: Request, exc: AlreadyMemberException):
    """AlreadyMemberException 처리: 이미 파티 멤버인 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def already_applied_handler(request: Request, exc: AlreadyAppliedException):
    """AlreadyAppliedException 처리: 이미 신청한 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def pod_access_denied_handler(request: Request, exc: PodAccessDeniedException):
    """PodAccessDeniedException 처리: 파티 접근이 거부된 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def review_already_exists_handler(
    request: Request, exc: ReviewAlreadyExistsException
):
    """ReviewAlreadyExistsException 처리: 이미 후기를 작성한 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def review_not_found_handler(request: Request, exc: ReviewNotFoundException):
    """ReviewNotFoundException 처리: 후기를 찾을 수 없는 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def review_permission_denied_handler(
    request: Request, exc: ReviewPermissionDeniedException
):
    """ReviewPermissionDeniedException 처리: 후기 수정/삭제 권한이 없는 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def invalid_image_handler(request: Request, exc: InvalidImageException):
    """InvalidImageException 처리: 이미지가 유효하지 않은 경우"""

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


# 자동 등록을 위한 핸들러 매핑
# 이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
EXCEPTION_HANDLERS = {
    PodNotFoundException: pod_not_found_handler,
    NoPodAccessPermissionException: no_pod_access_permission_handler,
    PodAlreadyClosedException: pod_already_closed_handler,
    PodIsFullException: pod_is_full_handler,
    AlreadyMemberException: already_member_handler,
    AlreadyAppliedException: already_applied_handler,
    PodAccessDeniedException: pod_access_denied_handler,
    ReviewAlreadyExistsException: review_already_exists_handler,
    ReviewNotFoundException: review_not_found_handler,
    ReviewPermissionDeniedException: review_permission_denied_handler,
    InvalidImageException: invalid_image_handler,
}
