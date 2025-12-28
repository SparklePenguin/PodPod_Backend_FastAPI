from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from .schedule_content_dto import ScheduleContentDto
from .schedule_member_dto import ScheduleMemberDto
from .schedule_type_enum import ScheduleTypeEnum


class ArtistScheduleDto(BaseModel):
    """아티스트 스케줄 DTO"""

    id: int = Field()
    artist_id: int | None = Field(default=None, alias="artistId")
    unit_id: int | None = Field(default=None, alias="unitId")
    artist_ko_name: str = Field(alias="artistKoName")
    type: ScheduleTypeEnum = Field()
    start_time: int = Field(
        ..., alias="startTime", description="일정 시작 시간 (밀리초)"
    )
    end_time: int = Field(..., alias="endTime", description="일정 종료 시간 (밀리초)")
    text: str | None = Field(default=None)
    title: str = Field()
    channel: str | None = Field(default=None)
    location: str | None = Field(default=None)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    # 관계 데이터
    members: List[ScheduleMemberDto] = Field(default_factory=list)
    contents: List[ScheduleContentDto] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
