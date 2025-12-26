"""
Pods 도메인 전용 Exception Handler

이 모듈은 Pods 도메인의 예외를 처리하는 핸들러를 정의합니다.
각 핸들러는 BaseResponse 패턴으로 일관된 응답을 반환합니다.

중요: 이 파일은 반드시 EXCEPTION_HANDLERS 딕셔너리를 export해야 합니다.
     이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.schemas import BaseResponse
from app.features.pods.exceptions import (
    InvalidPodStatusException,
    PodAlreadyJoinedException,
    PodApplicationAlreadyExistsException,
    PodApplicationNotFoundException,
    PodClosedException,
    PodFullException,
    PodNotFoundException,
    PodNotHostException,
    PodReviewAlreadyExistsException,
    PodReviewNotAllowedException,
)

logger = logging.getLogger(__name__)


async def pod_not_found_handler(request: Request, exc: PodNotFoundException):
    """PodNotFoundException 처리: 파티를 찾을 수 없는 경우"""
    logger.warning(f"Pod not found: pod_id={exc.pod_id}, path={request.url.path}")

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,  # Google Sheets에서 자동 로드
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def pod_full_handler(request: Request, exc: PodFullException):
    """PodFullException 처리: 파티 정원이 가득 찬 경우"""
    logger.warning(
        f"Pod full: pod_id={exc.pod_id}, "
        f"members={exc.current_members}/{exc.max_members}"
    )

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


async def pod_already_joined_handler(request: Request, exc: PodAlreadyJoinedException):
    """PodAlreadyJoinedException 처리: 이미 참여한 파티인 경우"""
    logger.warning(
        f"Already joined pod: pod_id={exc.pod_id}, user_id={exc.user_id}, "
        f"path={request.url.path}"
    )

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


async def pod_application_already_exists_handler(
    request: Request, exc: PodApplicationAlreadyExistsException
):
    """PodApplicationAlreadyExistsException 처리: 이미 신청한 파티인 경우"""
    logger.warning(
        f"Application already exists: pod_id={exc.pod_id}, user_id={exc.user_id}"
    )

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


async def pod_not_host_handler(request: Request, exc: PodNotHostException):
    """PodNotHostException 처리: 파티 호스트가 아닌 경우"""
    logger.warning(
        f"Not pod host: pod_id={exc.pod_id}, user_id={exc.user_id}, "
        f"path={request.url.path}"
    )

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


async def pod_closed_handler(request: Request, exc: PodClosedException):
    """PodClosedException 처리: 종료된 파티인 경우"""
    logger.warning(f"Pod closed: pod_id={exc.pod_id}, path={request.url.path}")

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


async def pod_application_not_found_handler(
    request: Request, exc: PodApplicationNotFoundException
):
    """PodApplicationNotFoundException 처리: 파티 신청을 찾을 수 없는 경우"""
    logger.warning(
        f"Pod application not found: application_id={exc.application_id}, "
        f"path={request.url.path}"
    )

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


async def invalid_pod_status_handler(request: Request, exc: InvalidPodStatusException):
    """InvalidPodStatusException 처리: 유효하지 않은 파티 상태인 경우"""
    logger.warning(
        f"Invalid pod status: pod_id={exc.pod_id}, "
        f"current={exc.current_status}, required={exc.required_status}"
    )

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


async def pod_review_already_exists_handler(
    request: Request, exc: PodReviewAlreadyExistsException
):
    """PodReviewAlreadyExistsException 처리: 이미 리뷰를 작성한 경우"""
    logger.warning(
        f"Pod review already exists: pod_id={exc.pod_id}, user_id={exc.user_id}"
    )

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


async def pod_review_not_allowed_handler(
    request: Request, exc: PodReviewNotAllowedException
):
    """PodReviewNotAllowedException 처리: 리뷰 작성 권한이 없는 경우"""
    logger.warning(
        f"Pod review not allowed: pod_id={exc.pod_id}, user_id={exc.user_id}, "
        f"reason={exc.reason}"
    )

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
    PodFullException: pod_full_handler,
    PodAlreadyJoinedException: pod_already_joined_handler,
    PodApplicationAlreadyExistsException: pod_application_already_exists_handler,
    PodNotHostException: pod_not_host_handler,
    PodClosedException: pod_closed_handler,
    PodApplicationNotFoundException: pod_application_not_found_handler,
    InvalidPodStatusException: invalid_pod_status_handler,
    PodReviewAlreadyExistsException: pod_review_already_exists_handler,
    PodReviewNotAllowedException: pod_review_not_allowed_handler,
}
