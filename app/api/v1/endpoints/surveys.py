from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user_id
from app.services.tendency_service import TendencyService
from app.schemas.tendency import TendencySurveyDto, SubmitTendencyTestRequest, Tendency
from app.schemas.common import SuccessResponse, ErrorResponse

router = APIRouter()


def get_tendency_service(db: AsyncSession = Depends(get_db)) -> TendencyService:
    return TendencyService(db)


# - MARK: 공개 API
@router.get(
    "/tendency-test",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "성향 테스트 설문 조회 성공"},
        404: {"model": ErrorResponse, "description": "성향 테스트 설문을 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
    summary="성향 테스트 설문 조회",
    description="성향 테스트 설문을 조회합니다.",
)
async def get_tendency_test_survey(
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    """성향 테스트 설문 조회"""
    try:
        survey = await tendency_service.get_tendency_survey()
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="tendency_survey_not_found",
                    status=status.HTTP_404_NOT_FOUND,
                    message="성향 테스트 설문을 찾을 수 없습니다.",
                ).model_dump(),
            )
        return SuccessResponse(
            code=200,
            message="tendency_survey_retrieved_successfully",
            data=survey,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="tendency_survey_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


# - MARK: 인증 필요 API
@router.post(
    "/tendency-test",
    response_model=SuccessResponse,
    responses={
        200: {"model": Tendency, "description": "성향 테스트 제출 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
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
    try:
        # 답변을 딕셔너리 형태로 변환
        answers_dict = {
            answer.question_id: answer.id for answer in score_request.answers
        }

        # 점수 계산
        calculation_result = await tendency_service.calculate_tendency_score(
            answers_dict
        )

        # 결과 저장
        await tendency_service.save_user_tendency_result(
            current_user_id, calculation_result["tendency_type"], answers_dict
        )

        # Tendency 객체 생성
        tendency = await tendency_service.calculate_tendency_score_flutter(
            [
                {"questionId": answer.question_id, "id": answer.id}
                for answer in score_request.answers
            ]
        )

        return SuccessResponse(
            code=200,
            message="tendency_test_submitted_successfully",
            data=tendency,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="tendency_test_submission_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )
