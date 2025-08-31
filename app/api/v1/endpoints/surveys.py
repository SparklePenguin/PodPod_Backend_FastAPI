from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.tendency_service import TendencyService
from app.schemas.tendency import TendencySurveyDto
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
            data=survey.model_dump(),
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
