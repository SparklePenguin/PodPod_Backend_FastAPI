from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db
from app.services.tendency_service import TendencyService
from app.schemas.common import SuccessResponse, ErrorResponse

router = APIRouter()


def get_tendency_service(db=Depends(get_db)) -> TendencyService:
    return TendencyService(db)


# - MARK: 공개 API
@router.get(
    "/results",
    response_model=SuccessResponse,
    responses={
        200: {
            "model": SuccessResponse,
            "description": "성향 테스트 결과 목록 조회 성공",
        },
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
    summary="성향 테스트 결과 목록 조회",
    description="모든 성향 테스트 결과를 조회합니다.",
)
async def get_tendency_results(
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    """성향 테스트 결과 목록 조회"""
    try:
        results = await tendency_service.get_tendency_results()
        return SuccessResponse(
            code=200,
            message="tendency_results_retrieved_successfully",
            data=results,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="tendency_results_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


@router.get(
    "/results/{tendency_type}",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "성향 테스트 결과 조회 성공"},
        404: {"model": ErrorResponse, "description": "성향 테스트 결과를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
    summary="특정 성향 테스트 결과 조회",
    description="특정 성향 테스트 결과를 조회합니다.",
)
async def get_tendency_result(
    tendency_type: str,
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    """특정 성향 테스트 결과 조회"""
    try:
        result = await tendency_service.get_tendency_result(tendency_type)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="tendency_result_not_found",
                    status=status.HTTP_404_NOT_FOUND,
                    message="성향 테스트 결과를 찾을 수 없습니다.",
                ).model_dump(),
            )
        return SuccessResponse(
            code=200,
            message="tendency_result_retrieved_successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="tendency_result_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


# - MARK: 내부용 API
@router.post(
    "/mvp",
    response_model=SuccessResponse,
    responses={
        200: {
            "model": SuccessResponse,
            "description": "성향 테스트 설문, 결과 데이터 생성 성공",
        },
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
    tags=["internal"],
    summary="성향 테스트 설문, 결과 데이터 생성 (내부용)",
    description="⚠️ 내부용 API - 성향 테스트 설문과 결과 데이터를 생성합니다. 개발/테스트 목적으로만 사용됩니다.",
)
async def create_mvp_tendency_data(
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    """성향 테스트 설문, 결과 데이터 생성 (내부용)"""
    try:
        result = await tendency_service.create_mvp_tendency_data()
        return SuccessResponse(
            code=200,
            message="mvp_tendency_data_created_successfully",
            data=result,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="mvp_tendency_data_creation_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )
