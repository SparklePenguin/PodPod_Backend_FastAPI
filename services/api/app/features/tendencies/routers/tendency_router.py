from fastapi import APIRouter, Depends

from app.deps.database import get_session
from app.common.schemas import BaseResponse
from app.core.http_status import HttpStatus
from app.features.tendencies.services.tendency_service import TendencyService

router = APIRouter()


def get_tendency_service(db=Depends(get_session)) -> TendencyService:
    return TendencyService(db)


# - MARK: 공개 API
@router.get(
    "/results",
    response_model=BaseResponse[dict],
    description="모든 성향 테스트 결과를 조회합니다.",
)
async def get_tendency_results(
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    results = await tendency_service.get_tendency_results()
    return BaseResponse.ok(data=results)


@router.get(
    "/results/{tendency_type}",
    response_model=BaseResponse[dict],
    description="특정 성향 테스트 결과를 조회합니다.",
)
async def get_tendency_result(
    tendency_type: str,
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    result = await tendency_service.get_tendency_result(tendency_type)
    if not result:
        from app.features.tendencies.exceptions import TendencyResultNotFoundException

        raise TendencyResultNotFoundException(tendency_type)
    return BaseResponse.ok(data=result)


# - MARK: 내부용 API
@router.post(
    "/mvp",
    response_model=BaseResponse[dict],
    description="⚠️ 내부용 API - 성향 테스트 설문과 결과 데이터를 생성합니다. 개발/테스트 목적으로만 사용됩니다.",
    tags=["internal"],
)
async def create_mvp_tendency_data(
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    result = await tendency_service.create_mvp_tendency_data()
    return BaseResponse.ok(data=result)
