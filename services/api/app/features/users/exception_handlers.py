"""
Users 도메인 전용 Exception Handler

이 모듈은 Users 도메인의 예외를 처리하는 핸들러를 정의합니다.
각 핸들러는 BaseResponse 패턴으로 일관된 응답을 반환합니다.

중요: 이 파일은 반드시 EXCEPTION_HANDLERS 딕셔너리를 export해야 합니다.
     이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.schemas import BaseResponse
from app.features.users.exceptions import (
    ArtistNotFoundException,
    EmailAlreadyExistsException,
    EmailRequiredException,
    SameOAuthProviderExistsException,
    UserNotFoundException,
)

logger = logging.getLogger(__name__)


async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    """UserNotFoundException 처리: 사용자를 찾을 수 없는 경우"""
    logger.warning(f"User not found: user_id={exc.user_id}, path={request.url.path}")

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


async def email_required_handler(request: Request, exc: EmailRequiredException):
    """EmailRequiredException 처리: 이메일이 필수인데 제공되지 않은 경우"""
    logger.warning(f"Email required: path={request.url.path}")

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


async def email_already_exists_handler(
    request: Request, exc: EmailAlreadyExistsException
):
    """EmailAlreadyExistsException 처리: 이미 존재하는 이메일인 경우"""
    logger.warning(f"Email already exists: email={exc.email}, path={request.url.path}")

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


async def same_oauth_provider_exists_handler(
    request: Request, exc: SameOAuthProviderExistsException
):
    """SameOAuthProviderExistsException 처리: 같은 OAuth 제공자의 계정이 이미 존재하는 경우"""
    logger.warning(
        f"Same OAuth provider exists: provider={exc.provider}, path={request.url.path}"
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


async def artist_not_found_handler(request: Request, exc: ArtistNotFoundException):
    """ArtistNotFoundException 처리: 아티스트를 찾을 수 없는 경우 (선호 아티스트 관련)"""
    logger.warning(
        f"Artist not found: artist_id={exc.artist_id}, path={request.url.path}"
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
    UserNotFoundException: user_not_found_handler,
    EmailRequiredException: email_required_handler,
    EmailAlreadyExistsException: email_already_exists_handler,
    SameOAuthProviderExistsException: same_oauth_provider_exists_handler,
    ArtistNotFoundException: artist_not_found_handler,
}
