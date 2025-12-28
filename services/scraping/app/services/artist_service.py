from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.artist_repository import ArtistRepository
from ..repositories.artist_schedule_repository import ArtistScheduleRepository


class ArtistService:
    def __init__(self, db: AsyncSession):
        self.artist_crud = ArtistRepository(db)
        self.schedule_crud = ArtistScheduleRepository(db)

    # - MARK: (내부용) BLIP+MVP 병합 동기화
    async def sync_blip_and_mvp(self) -> dict:
        """BLIP 전체 데이터와 MVP 이름 목록을 병합하여 DB에 동기화"""
        return await self.artist_crud.sync_from_blip_and_mvp()

    # - MARK: (내부용) JSON에서 스케줄 가져오기
    async def import_schedules_from_json(
        self, schedule_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """JSON 데이터에서 스케줄 가져오기"""
        return await self.schedule_crud.import_schedules_from_json(schedule_data)
