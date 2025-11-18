from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user_id
from app.services.tendency_service import TendencyService
from app.schemas.tendency import TendencySurveyDto, SubmitTendencyTestRequest, Tendency
from app.schemas.common import BaseResponse
from app.core.http_status import HttpStatus

router = APIRouter()


def get_tendency_service(db: AsyncSession = Depends(get_db)) -> TendencyService:
    return TendencyService(db)


# - MARK: 공개 API
@router.get(
    "/tendency-test",
    response_model=BaseResponse[TendencySurveyDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[TendencySurveyDto],
            "description": "성향 테스트 설문 조회 성공",
        },
    },
    summary="성향 테스트 설문 조회",
    description="성향 테스트 설문을 조회합니다.",
)
async def get_tendency_test_survey(
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    """성향 테스트 설문 조회"""
    survey = await tendency_service.get_tendency_survey()
    if not survey:
        return BaseResponse.error(
            code=HttpStatus.NOT_FOUND,
            message="성향 테스트 설문을 찾을 수 없습니다.",
        )
    return BaseResponse.ok(data=survey.model_dump(by_alias=True))


# - MARK: 인증 필요 API
@router.post(
    "/tendency-test",
    response_model=BaseResponse[Tendency],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[Tendency],
            "description": "성향 테스트 제출 성공",
        },
    },
    summary="성향 테스트 제출",
    description="성향 테스트 답변을 제출하고 결과를 저장합니다.",
)
async def submit_tendency_test(
    score_request: SubmitTendencyTestRequest,
    current_user_id: int = Depends(get_current_user_id),
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    """성향 테스트 제출"""
    # 답변을 딕셔너리 형태로 변환
    answers_dict = {answer.question_id: answer.id for answer in score_request.answers}

    # 점수 계산
    calculation_result = await tendency_service.calculate_tendency_score(answers_dict)

    # 결과 저장
    await tendency_service.save_user_tendency_result(
        current_user_id, calculation_result["tendency_type"], answers_dict
    )

    # Tendency 객체 생성
    tendency = await tendency_service.calculate_tendency_score_flutter(
        [
            {"questionId": answer.question_id, "answerId": answer.id}
            for answer in score_request.answers
        ]
    )

    return BaseResponse.ok(data=tendency.model_dump(by_alias=True))
