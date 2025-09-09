from fastapi import APIRouter, Query
from app.schemas.common import SuccessResponse, ErrorResponse
from app.schemas.schedule import ArtistScheduleDto
from app.services.artist_schedule_service import ArtistScheduleService


router = APIRouter()


@router.get(
    "/artist/schedule",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "아티스트 일정 샘플 조회 성공"},
        404: {"model": ErrorResponse, "description": "아티스트를 찾을 수 없음"},
    },
    summary="아티스트 일정 샘플",
    description="아티스트 ID로 일정 데이터를 반환합니다.",
)
async def get_artist_schedule_sample(
    artist_id: int = Query(..., description="아티스트 ID")
):
    sample = ArtistScheduleService.get_sample_schedule(artist_id)
    return SuccessResponse(code=200, message="schedule_sample", data=sample)
