from typing import List

from app.common.schemas import BaseResponse
from app.deps.service import get_tendency_use_case
from app.features.tendencies.exceptions import TendencyResultNotFoundException
from app.features.tendencies.schemas import TendencyResultDto
from app.features.tendencies.use_cases.tendency_use_case import TendencyUseCase
from fastapi import APIRouter, Depends

router = APIRouter()


# - MARK: 모든 성향 테스트 결과 조회
@router.get(
    "/results",
    response_model=BaseResponse[List[TendencyResultDto]],
    description="모든 성향 테스트 결과 조회",
)
async def get_tendency_results(
    tendency_use_case: TendencyUseCase = Depends(get_tendency_use_case),
):
    results = await tendency_use_case.get_tendency_results()
    return BaseResponse.ok(data=results)


# - MARK: 특정 성향 테스트 결과 조회
@router.get(
    "/results/{tendency_type}",
    response_model=BaseResponse[TendencyResultDto],
    description="성향 테스트 결과 조회",
)
async def get_tendency_result(
    tendency_type: str,
    tendency_use_case: TendencyUseCase = Depends(get_tendency_use_case),
):
    result = await tendency_use_case.get_tendency_result(tendency_type)
    if not result:
        raise TendencyResultNotFoundException(tendency_type)
    return BaseResponse.ok(data=result)
