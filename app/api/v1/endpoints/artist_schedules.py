from fastapi import APIRouter, Query
from app.schemas.common import BaseResponse
from app.schemas.schedule import ArtistScheduleDto
from app.services.artist_schedule_service import ArtistScheduleService
from app.core.http_status import HttpStatus


router = APIRouter()


# - MARK: 아티스트 일정 샘플 조회
@router.get(
    "",
    response_model=BaseResponse[ArtistScheduleDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[ArtistScheduleDto],
            "description": "아티스트 일정 샘플 조회 성공",
        },
    },
    summary="아티스트 일정 샘플",
    description="아티스트 ID로 일정 데이터를 반환합니다.",
)
async def get_artist_schedule_sample(
    artist_id: int = Query(..., description="아티스트 ID")
):
    sample = ArtistScheduleService.get_sample_schedule(artist_id)
    return BaseResponse.ok(data=sample)
