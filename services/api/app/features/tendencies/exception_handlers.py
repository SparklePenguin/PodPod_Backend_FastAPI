"""
Tendencies 도메인 전용 Exception Handler

이 모듈은 Tendencies 도메인의 예외를 처리하는 핸들러를 정의합니다.
각 핸들러는 BaseResponse 패턴으로 일관된 응답을 반환합니다.

중요: 이 파일은 반드시 EXCEPTION_HANDLERS 딕셔너리를 export해야 합니다.
     이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
"""

import logging

from app.common.schemas import BaseResponse
from app.features.tendencies.exceptions import (
    TendencyResultNotFoundException,
    TendencySurveyNotFoundException,
)
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def tendency_result_not_found_handler(
    request: Request, exc: TendencyResultNotFoundException
):
    """TendencyResultNotFoundException 처리: 성향 테스트 결과를 찾을 수 없는 경우"""
    logger.warning(
        f"Tendency result not found: tendency_type={exc.tendency_type}, path={request.url.path}"
    )

    response = BaseResponse(
        data=None,
        error_key=exc.error_key,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(by_alias=True)
    )


async def tendency_survey_not_found_handler(
    request: Request, exc: TendencySurveyNotFoundException
):
    """TendencySurveyNotFoundException 처리: 성향 테스트 설문을 찾을 수 없는 경우"""
    logger.warning(f"Tendency survey not found: path={request.url.path}")

    response = BaseResponse(
        data=None,
        error_key=exc.error_key,
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
    TendencyResultNotFoundException: tendency_result_not_found_handler,
    TendencySurveyNotFoundException: tendency_survey_not_found_handler,
}
