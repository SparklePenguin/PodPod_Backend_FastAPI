from app.common.schemas import BaseResponse, PageDto
from app.deps.providers import get_schedule_by_id_use_case, get_schedules_use_case
from app.features.artists.schemas import ArtistScheduleDto
from app.features.artists.use_cases.artist_schedule_use_cases import (
    GetScheduleByIdUseCase,
    GetSchedulesUseCase,
)
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/artist/schedules", tags=["artist-schedules"])


# - MARK: 아티스트 스케줄 목록 조회
@router.get(
    "",
    response_model=BaseResponse[PageDto[ArtistScheduleDto]],
    description="아티스트 스케줄 목록 조회",
)
async def get_artist_schedules(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    artist_id: int | None = Query(None, description="아티스트 ID 필터"),
    unit_id: int | None = Query(None, description="아티스트 유닛 ID 필터"),
    schedule_type: int | None = Query(None, description="스케줄 유형 필터"),
    use_case: GetSchedulesUseCase = Depends(get_schedules_use_case),
):
    result = await use_case.execute(page, size, artist_id, unit_id, schedule_type)
    return BaseResponse.ok(result, message_ko="아티스트 스케줄 목록 조회 성공")


# - MARK: 아티스트 스케줄 상세 정보 조회
@router.get(
    "/{schedule_id}",
    response_model=BaseResponse[ArtistScheduleDto],
    description="아티스트 스케줄 상세 정보 조회",
)
async def get_artist_schedule(
    schedule_id: int,
    use_case: GetScheduleByIdUseCase = Depends(get_schedule_by_id_use_case),
):
    result = await use_case.execute(schedule_id)
    return BaseResponse.ok(result, message_ko="아티스트 스케줄 상세 조회 성공")
