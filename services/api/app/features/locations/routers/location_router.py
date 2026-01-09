from typing import List

from app.common.schemas import BaseResponse
from app.deps.providers import get_location_use_case
from app.features.locations.schemas import LocationDto
from app.features.locations.use_cases import LocationUseCase
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/regions", tags=["regions"])


# - MARK: 모든 지역 정보 조회
@router.get(
    "",
    response_model=BaseResponse[List[LocationDto]],
    description="전체 지역 정보와 인기 지역 정보 조회 (인기 지역이 맨 앞에 표시)",
)
async def get_all_locations(
    use_case: LocationUseCase = Depends(get_location_use_case),
):
    result = await use_case.get_all_locations()
    return BaseResponse.ok(data=result)
