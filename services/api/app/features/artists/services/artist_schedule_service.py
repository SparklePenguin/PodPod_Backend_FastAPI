from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PageDto
from app.features.artists.exceptions import ArtistScheduleNotFoundException
from app.features.artists.repositories.artist_schedule_repository import (
    ArtistScheduleRepository,
)
from app.features.artists.schemas import ArtistScheduleDto


class ArtistScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.aritst_sche_repo = ArtistScheduleRepository(db)

    async def get_schedule_by_id(self, schedule_id: int) -> ArtistScheduleDto:
        """ID로 스케줄 조회"""
        schedule = await self.aritst_sche_repo.get_schedule_by_id(schedule_id)
        if not schedule:
            raise ArtistScheduleNotFoundException(schedule_id)
        return ArtistScheduleDto.model_validate(schedule, from_attributes=True)

    async def get_schedules(
        self,
        page: int = 1,
        size: int = 20,
        artist_id: int | None = None,
        unit_id: int | None = None,
        schedule_type: int | None = None,
    ) -> PageDto[ArtistScheduleDto]:
        """스케줄 목록 조회"""
        schedules, total_count = await self.aritst_sche_repo.get_schedules(
            page=page,
            size=size,
            artist_id=artist_id,
            unit_id=unit_id,
            schedule_type=schedule_type,
        )

        # DTO 변환
        schedule_dtos = [
            ArtistScheduleDto.model_validate(schedule, from_attributes=True)
            for schedule in schedules
        ]

        # PageDto 생성
        return PageDto.create(
            items=schedule_dtos, page=page, size=size, total_count=total_count
        )
