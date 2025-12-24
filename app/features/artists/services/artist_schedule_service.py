from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.artists.repositories.schedule_repository import ArtistScheduleCRUD
from app.features.artists.schemas.artist_schedule_schemas import (
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
        size: int = 20,
        artist_id: Optional[int] = None,
        unit_id: Optional[int] = None,
        schedule_type: Optional[int] = None,
    ) -> Dict[str, Any]:
        """스케줄 목록 조회"""
        result = await self.crud.get_schedules(
            page=page,
            size=size,
            artist_id=artist_id,
            unit_id=unit_id,
            schedule_type=schedule_type,
        )

        # DTO 변환
        result["items"] = [
            self._convert_to_dto(schedule) for schedule in result["items"]
        ]

        # 페이지네이션 필드 추가
        result["currentPage"] = result["page"]
        result["hasNext"] = result["page"] < result["total_pages"]
        result["hasPrev"] = result["page"] > 1

        return result

    async def import_schedules_from_json(
        self, schedule_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """JSON 데이터에서 스케줄 가져오기"""
        return await self.crud.import_schedules_from_json(schedule_data)

    def _convert_to_dto(self, schedule) -> ArtistScheduleDto:
        """엔터티를 DTO로 변환"""
        from app.features.artists.schemas.artist_schedule_schemas import ScheduleTypeEnum
        from datetime import datetime, timezone
        
        schedule_type_value = getattr(schedule, "type", None)
        if schedule_type_value is None:
            schedule_type = ScheduleTypeEnum.GENERAL_CONTENT  # 기본값
        else:
            try:
                schedule_type = ScheduleTypeEnum(schedule_type_value)
            except (ValueError, TypeError):
                schedule_type = ScheduleTypeEnum.GENERAL_CONTENT  # 기본값
        
        created_at_value = getattr(schedule, "created_at", None)
        if created_at_value is None:
            created_at_value = datetime.now(timezone.utc).replace(tzinfo=None)
        
        updated_at_value = getattr(schedule, "updated_at", None)
        if updated_at_value is None:
            updated_at_value = datetime.now(timezone.utc).replace(tzinfo=None)
        
        return ArtistScheduleDto(
            id=getattr(schedule, "id", 0),
            artist_id=getattr(schedule, "artist_id", None),
            unit_id=getattr(schedule, "unit_id", None),
            artist_ko_name=getattr(schedule, "artist_ko_name", ""),  # 필드명 사용
            type=schedule_type,
            start_time=getattr(schedule, "start_time", 0),
            end_time=getattr(schedule, "end_time", 0),
            text=getattr(schedule, "text", None),
            title=getattr(schedule, "title", ""),
            channel=getattr(schedule, "channel", None),
            location=getattr(schedule, "location", None),
            created_at=created_at_value,  # 필드명 사용
            updated_at=updated_at_value,  # 필드명 사용
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
