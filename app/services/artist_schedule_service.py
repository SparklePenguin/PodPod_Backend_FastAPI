from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.artist_schedule import ArtistScheduleCRUD
from app.schemas.artist_schedule import (
    ArtistScheduleCreateRequest,
    ArtistScheduleDto,
    ScheduleMemberDto,
    ScheduleContentDto,
)


class ArtistScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = ArtistScheduleCRUD(db)

    async def create_schedule(
        self, request: ArtistScheduleCreateRequest
    ) -> ArtistScheduleDto:
        """아티스트 스케줄 생성"""
        schedule = await self.crud.create_schedule(request)
        return self._convert_to_dto(schedule)

    async def get_schedule_by_id(self, schedule_id: int) -> Optional[ArtistScheduleDto]:
        """ID로 스케줄 조회"""
        schedule = await self.crud.get_schedule_by_id(schedule_id)
        if not schedule:
            return None
        return self._convert_to_dto(schedule)

    async def get_schedules(
        self,
        page: int = 1,
        page_size: int = 20,
        artist_id: Optional[int] = None,
        unit_id: Optional[int] = None,
        schedule_type: Optional[int] = None,
    ) -> Dict[str, Any]:
        """스케줄 목록 조회"""
        result = await self.crud.get_schedules(
            page=page,
            page_size=page_size,
            artist_id=artist_id,
            unit_id=unit_id,
            schedule_type=schedule_type,
        )

        # DTO 변환
        result["items"] = [
            self._convert_to_dto(schedule) for schedule in result["items"]
        ]

        return result

    async def import_schedules_from_json(
        self, schedule_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """JSON 데이터에서 스케줄 가져오기"""
        return await self.crud.import_schedules_from_json(schedule_data)

    def _convert_to_dto(self, schedule) -> ArtistScheduleDto:
        """엔터티를 DTO로 변환"""
        return ArtistScheduleDto(
            id=schedule.id,
            artist_id=schedule.artist_id,
            unit_id=schedule.unit_id,
            artist_ko_name=schedule.artist_ko_name,
            type=schedule.type,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            text=schedule.text,
            title=schedule.title,
            channel=schedule.channel,
            location=schedule.location,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
            members=[
                ScheduleMemberDto(
                    id=member.id,
                    ko_name=member.ko_name,
                    en_name=member.en_name,
                    artist_id=member.artist_id,
                )
                for member in schedule.members
            ],
            contents=[
                ScheduleContentDto(
                    id=content.id,
                    type=content.type,
                    path=content.path,
                    title=content.title,
                )
                for content in schedule.contents
            ],
        )
