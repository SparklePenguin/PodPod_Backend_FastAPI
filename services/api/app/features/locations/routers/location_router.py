from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse
from app.core.database import get_session
from app.core.http_status import HttpStatus
from app.features.locations.schemas import (
    LocationDto,
    LocationResponse,
)
from app.features.locations.services.location_service import LocationService

router = APIRouter()


def get_location_service(db: AsyncSession = Depends(get_session)) -> LocationService:
    return LocationService(db)


# - MARK: 모든 지역 정보 조회
@router.get(
    "",
    response_model=BaseResponse[List[LocationResponse]],
    description="전체 지역 정보와 인기 지역 정보를 조회합니다. (인기 지역이 맨 앞에 표시됩니다)",
    tags=["regions"],
)
async def get_all_locations(
    service: LocationService = Depends(get_location_service),
):
    locations = await service.get_all_locations()
    return BaseResponse.ok(locations, message_ko="지역 정보 조회 성공", http_status=200)


# - MARK: JSON 파일에서 지역 데이터 생성
@router.post(
    "/import",
    response_model=BaseResponse[List[LocationDto]],
    description="mvp/locations.json 파일을 읽어서 지역 데이터를 생성합니다.",
    tags=["regions"],
)
async def create_locations_from_json(
    service: LocationService = Depends(get_location_service),
):
    created_locations = await service.create_locations_from_json()
    return BaseResponse.ok(
        created_locations, message_ko="지역 데이터 생성 성공", http_status=201
    )
