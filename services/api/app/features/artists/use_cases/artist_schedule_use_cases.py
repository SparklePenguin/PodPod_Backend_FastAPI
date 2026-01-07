"""아티스트 스케줄 관련 Use Cases"""

from app.common.schemas import PageDto
from app.features.artists.exceptions import ArtistScheduleNotFoundException
from app.features.artists.repositories.artist_schedule_repository import (
    ArtistScheduleRepository,
)
from app.features.artists.schemas import ArtistScheduleDto
from app.features.artists.services.artist_dto_service import ArtistDtoService
from sqlalchemy.ext.asyncio import AsyncSession


class GetScheduleByIdUseCase:
    """ID로 스케줄 조회 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.schedule_repo = ArtistScheduleRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(self, schedule_id: int) -> ArtistScheduleDto:
        """ID로 스케줄 조회"""
        schedule = await self.schedule_repo.get_schedule_by_id(schedule_id)
        if not schedule:
            raise ArtistScheduleNotFoundException(schedule_id)
        return self.dto_service.to_schedule_dto(schedule)


class GetSchedulesUseCase:
    """스케줄 목록 조회 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.schedule_repo = ArtistScheduleRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(
        self,
        page: int = 1,
        size: int = 20,
        artist_id: int | None = None,
        unit_id: int | None = None,
        schedule_type: int | None = None,
    ) -> PageDto[ArtistScheduleDto]:
        """스케줄 목록 조회"""
        schedules, total_count = await self.schedule_repo.get_schedules(
            page=page,
            size=size,
            artist_id=artist_id,
            unit_id=unit_id,
            schedule_type=schedule_type,
        )

        schedule_dtos = self.dto_service.to_schedule_dtos(schedules)

        return PageDto.create(
            items=schedule_dtos, page=page, size=size, total_count=total_count
        )
