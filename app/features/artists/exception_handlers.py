"""
Artists 도메인 전용 Exception Handler

이 모듈은 Artists 도메인의 예외를 처리하는 핸들러를 정의합니다.
각 핸들러는 BaseResponse 패턴으로 일관된 응답을 반환합니다.

중요: 이 파일은 반드시 EXCEPTION_HANDLERS 딕셔너리를 export해야 합니다.
     이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.schemas import BaseResponse
from app.features.artists.exceptions import (
    ArtistAlreadyExistsException,
    ArtistNotFoundException,
    ArtistScheduleNotFoundException,
    ArtistSuggestionNotFoundException,
)

logger = logging.getLogger(__name__)


async def artist_not_found_handler(request: Request, exc: ArtistNotFoundException):
    """ArtistNotFoundException 처리: 아티스트를 찾을 수 없는 경우"""
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


async def artist_schedule_not_found_handler(
    request: Request, exc: ArtistScheduleNotFoundException
):
    """ArtistScheduleNotFoundException 처리: 아티스트 스케줄을 찾을 수 없는 경우"""
    logger.warning(
        f"Artist schedule not found: schedule_id={exc.schedule_id}, "
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


async def artist_suggestion_not_found_handler(
    request: Request, exc: ArtistSuggestionNotFoundException
):
    """ArtistSuggestionNotFoundException 처리: 아티스트 추천을 찾을 수 없는 경우"""
    logger.warning(
        f"Artist suggestion not found: suggestion_id={exc.suggestion_id}, "
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


async def artist_already_exists_handler(
    request: Request, exc: ArtistAlreadyExistsException
):
    """ArtistAlreadyExistsException 처리: 이미 존재하는 아티스트인 경우"""
    logger.warning(
        f"Artist already exists: artist_name={exc.artist_name}, "
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


# 자동 등록을 위한 핸들러 매핑
# 이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
EXCEPTION_HANDLERS = {
    ArtistNotFoundException: artist_not_found_handler,
    ArtistScheduleNotFoundException: artist_schedule_not_found_handler,
    ArtistSuggestionNotFoundException: artist_suggestion_not_found_handler,
    ArtistAlreadyExistsException: artist_already_exists_handler,
}
