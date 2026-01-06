from typing import List

from app.common.schemas import BaseResponse
from app.deps.providers import get_location_service
from app.features.locations.schemas import LocationDto
from app.features.locations.services.location_service import LocationService
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/regions", tags=["regions"])


# - MARK: 모든 지역 정보 조회
@router.get(
    "",
    response_model=BaseResponse[List[LocationDto]],
    description="전체 지역 정보와 인기 지역 정보 조회 (인기 지역이 맨 앞에 표시)",
)
async def get_all_locations(
    service: LocationService = Depends(get_location_service),
):
    result = await service.get_all_locations()
    return BaseResponse.ok(data=result)
