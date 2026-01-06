from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.providers import get_tendency_use_case
from app.features.tendencies.schemas import (
    SubmitTendencyTestRequest,
    TendencyDto,
    TendencySurveyDto,
)
from app.features.tendencies.use_cases.tendency_use_case import TendencyUseCase
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/surveys", tags=["surveys"])


# - MARK: 성향 테스트 설문 조회
@router.get(
    "/tendency-test",
    response_model=BaseResponse[TendencySurveyDto],
    description="성향 테스트 설문 조회",
)
async def get_tendency_test_survey(
    tendency_use_case: TendencyUseCase = Depends(get_tendency_use_case),
):
    survey = await tendency_use_case.get_tendency_survey()
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
    tendency_use_case: TendencyUseCase = Depends(get_tendency_use_case),
):
    tendency = await tendency_use_case.submit_tendency_test(
        current_user_id, score_request
    )
    return BaseResponse.ok(data=tendency)
