from typing import Tuple

from app.features.artists.models.artist_schedule import ArtistSchedule
from sqlalchemy import and_, desc, func, select
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
        page: int = 1,
        size: int = 20,
        artist_id: int | None = None,
        unit_id: int | None = None,
        schedule_type: int | None = None,
    ) -> Tuple[list[ArtistSchedule], int]:
        """스케줄 목록 조회 (페이지네이션)"""
        # 기본 쿼리
        query = select(ArtistSchedule).options(
            selectinload(ArtistSchedule.members), selectinload(ArtistSchedule.contents)
        )

        # 필터 조건 추가
        conditions = []
        if artist_id is not None:
            conditions.append(ArtistSchedule.artist_id == artist_id)
        if unit_id is not None:
            conditions.append(ArtistSchedule.unit_id == unit_id)
        if schedule_type is not None:
            conditions.append(ArtistSchedule.type == schedule_type)

        if conditions:
            query = query.where(and_(*conditions))

        # 정렬 (최신순)
        query = query.order_by(desc(ArtistSchedule.start_time))

        # 전체 개수 조회
        count_query = select(func.count(ArtistSchedule.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_count = await self._session.scalar(count_query)

        # 페이지네이션
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self._session.execute(query)
        schedules = list(result.scalars().all())

        return (schedules, total_count or 0)
