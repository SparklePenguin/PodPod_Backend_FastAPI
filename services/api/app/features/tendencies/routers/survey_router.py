from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.service import get_tendency_service
from app.features.tendencies.schemas import (
    SubmitTendencyTestRequest,
    TendencyDto,
    TendencySurveyDto,
)
from app.features.tendencies.services.tendency_service import TendencyService
from fastapi import APIRouter, Depends

router = APIRouter()


# - MARK: 성향 테스트 설문 조회
@router.get(
    "/tendency-test",
    response_model=BaseResponse[TendencySurveyDto],
    description="성향 테스트 설문 조회",
)
async def get_tendency_test_survey(
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    survey = await tendency_service.get_tendency_survey()
    return BaseResponse.ok(data=survey)


# - MARK: 성향 테스트 제출
@router.post(
    "/tendency-test",
    response_model=BaseResponse[TendencyDto],
    description="성향 테스트 제출",
)
async def submit_tendency_test(
    score_request: SubmitTendencyTestRequest,
    current_user_id: int = Depends(get_current_user_id),
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    tendency = await tendency_service.submit_tendency_test(
        current_user_id, score_request
    )
    return BaseResponse.ok(data=tendency)
