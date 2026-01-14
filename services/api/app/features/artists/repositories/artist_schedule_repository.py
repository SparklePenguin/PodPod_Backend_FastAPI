from app.features.artists.models import ArtistSchedule
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ArtistScheduleRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: ID로 스케줄 조회
    async def get_schedule_by_id(self, schedule_id: int) -> ArtistSchedule | None:
        """ID로 스케줄 조회"""
        query = (
            select(ArtistSchedule)
            .options(
                selectinload(ArtistSchedule.members),
                selectinload(ArtistSchedule.contents),
            )
            .where(ArtistSchedule.id == schedule_id)
        )

        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    # - MARK: 스케줄 목록 조회
    async def get_schedules(
        self,
        year: int,
        month: int,
        artist_id: int | None = None,
        unit_id: int | None = None,
        schedule_type: int | None = None,
    ) -> list[ArtistSchedule]:
        """스케줄 목록 조회 (월별)"""
        from datetime import datetime

        # 해당 월의 시작일과 종료일 계산
        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month + 1, 1)

        # 기본 쿼리
        query = select(ArtistSchedule).options(
            selectinload(ArtistSchedule.members), selectinload(ArtistSchedule.contents)
        )

        # 필터 조건 추가
        conditions = [
            ArtistSchedule.start_time >= start_of_month,
            ArtistSchedule.start_time < end_of_month,
        ]
        if artist_id is not None:
            conditions.append(ArtistSchedule.artist_id == artist_id)
        if unit_id is not None:
            conditions.append(ArtistSchedule.unit_id == unit_id)
        if schedule_type is not None:
            conditions.append(ArtistSchedule.type == schedule_type)

        query = query.where(and_(*conditions))

        # 정렬 (시간순)
        query = query.order_by(ArtistSchedule.start_time)

        result = await self._session.execute(query)
        schedules = list(result.scalars().all())

        return schedules
