from fastapi import Depends, Query

from app.common.schemas import BaseResponse
from app.deps.providers import get_schedule_by_id_use_case, get_schedules_use_case
from app.features.artists.routers._base import ArtistSchedulerController
from app.features.artists.schemas import ArtistScheduleDto
from app.features.artists.use_cases.artist_schedule_use_cases import (
    GetScheduleByIdUseCase,
    GetSchedulesUseCase,
)


class ArtistScheduleRouter:

    @staticmethod
    @ArtistSchedulerController.ROUTER.get(
        "",
        response_model=BaseResponse[list[ArtistScheduleDto]],
        description="아티스트 스케줄 목록 조회 (월별)",
    )
    async def get_artist_schedules(
            year: int = Query(..., ge=2000, le=2100, description="조회할 년도"),
            month: int = Query(..., ge=1, le=12, description="조회할 월 (1~12)"),
            artist_id: int | None = Query(None, description="아티스트 ID 필터"),
            unit_id: int | None = Query(None, description="아티스트 유닛 ID 필터"),
            schedule_type: int | None = Query(None, description="스케줄 유형 필터"),
            use_case: GetSchedulesUseCase = Depends(get_schedules_use_case),
    ):
        result = await use_case.execute(year, month, artist_id, unit_id, schedule_type)
        return BaseResponse.ok(result, message_ko="아티스트 스케줄 목록 조회 성공")

    @staticmethod
    @ArtistSchedulerController.ROUTER.get(
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
