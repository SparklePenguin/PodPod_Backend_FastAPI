from typing import List

from pydantic import BaseModel, Field

from .schedule_content_create_request import ScheduleContentCreateRequest
from .schedule_member_create_request import ScheduleMemberCreateRequest
from .schedule_type_enum import ScheduleTypeEnum


class ArtistScheduleCreateRequest(BaseModel):
    """아티스트 스케줄 생성 요청"""

    artist_id: int | None = Field(None, description="아티스트 ID")
    unit_id: int | None = Field(None, description="아티스트 유닛 ID")
    artist_ko_name: str = Field(..., description="아티스트 한글명")
    type: ScheduleTypeEnum = Field(..., description="일정 유형")
    start_time: int = Field(..., description="일정 시작 시간 (밀리초)")
    end_time: int = Field(..., description="일정 종료 시간 (밀리초)")
    text: str | None = Field(None, description="일정 상세 설명")
    title: str = Field(..., description="일정 제목")
    channel: str | None = Field(None, description="방송 채널")
    location: str | None = Field(None, description="장소")

    # 관계 데이터
    members: List[ScheduleMemberCreateRequest] = []
    contents: List[ScheduleContentCreateRequest] = []
