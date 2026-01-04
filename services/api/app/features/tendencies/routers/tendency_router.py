from typing import List

from app.common.schemas import BaseResponse
from app.deps.service import get_tendency_service
from app.features.tendencies.schemas import TendencyResultDto
from app.features.tendencies.services.tendency_service import TendencyService
from fastapi import APIRouter, Depends

router = APIRouter()


# - MARK: 모든 성향 테스트 결과 조회
@router.get(
    "/results",
    response_model=BaseResponse[List[TendencyResultDto]],
    description="모든 성향 테스트 결과 조회",
)
async def get_tendency_results(
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    results = await tendency_service.get_tendency_results()
    return BaseResponse.ok(data=results)


# - MARK: 특정 성향 테스트 결과 조회
@router.get(
    "/results/{tendency_type}",
    response_model=BaseResponse[TendencyResultDto],
    description="성향 테스트 결과 조회",
)
async def get_tendency_result(
    tendency_type: str,
    tendency_service: TendencyService = Depends(get_tendency_service),
):
    result = await tendency_service.get_tendency_result(tendency_type)
    return BaseResponse.ok(data=result)
