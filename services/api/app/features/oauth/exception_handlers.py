"""
OAuth 도메인 전용 Exception Handler

이 모듈은 OAuth 도메인의 예외를 처리하는 핸들러를 정의합니다.
각 핸들러는 BaseResponse 패턴으로 일관된 응답을 반환합니다.

중요: 이 파일은 반드시 EXCEPTION_HANDLERS 딕셔너리를 export해야 합니다.
     이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.schemas import BaseResponse
from app.features.oauth.exceptions import (
    OAuthAuthenticationFailedException,
    OAuthProviderNotSupportedException,
    OAuthStateInvalidException,
    OAuthTokenInvalidException,
    OAuthUserInfoFailedException,
)

logger = logging.getLogger(__name__)


async def oauth_authentication_failed_handler(
    request: Request, exc: OAuthAuthenticationFailedException
):
    """OAuthAuthenticationFailedException 처리: OAuth 인증 실패"""
    logger.warning(
        f"OAuth authentication failed: provider={exc.provider}, "
        f"reason={exc.reason}, path={request.url.path}"
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


async def oauth_token_invalid_handler(
    request: Request, exc: OAuthTokenInvalidException
):
    """OAuthTokenInvalidException 처리: OAuth 토큰이 유효하지 않은 경우"""
    logger.warning(
        f"OAuth token invalid: provider={exc.provider}, path={request.url.path}"
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


async def oauth_user_info_failed_handler(
    request: Request, exc: OAuthUserInfoFailedException
):
    """OAuthUserInfoFailedException 처리: OAuth 사용자 정보 조회 실패"""
    logger.warning(
        f"OAuth user info failed: provider={exc.provider}, path={request.url.path}"
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


async def oauth_state_invalid_handler(request: Request, exc: OAuthStateInvalidException):
    """OAuthStateInvalidException 처리: OAuth state가 유효하지 않은 경우"""
    logger.warning(f"OAuth state invalid: path={request.url.path}")

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


async def oauth_provider_not_supported_handler(
    request: Request, exc: OAuthProviderNotSupportedException
):
    """OAuthProviderNotSupportedException 처리: 지원하지 않는 OAuth 제공자"""
    logger.warning(
        f"OAuth provider not supported: provider={exc.provider}, path={request.url.path}"
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
    OAuthAuthenticationFailedException: oauth_authentication_failed_handler,
    OAuthTokenInvalidException: oauth_token_invalid_handler,
    OAuthUserInfoFailedException: oauth_user_info_failed_handler,
    OAuthStateInvalidException: oauth_state_invalid_handler,
    OAuthProviderNotSupportedException: oauth_provider_not_supported_handler,
}
