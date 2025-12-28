from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ScheduleTypeEnum(int, Enum):
    """스케줄 유형 열거형"""

    GENERAL_CONTENT = 1  # 일반 콘텐츠 (영상, 방송 등)
    MUSIC_RELEASE = 2  # 음원/앨범 발매
    BIRTHDAY = 4  # 생일/기념일
    OTHER_EVENT = 5  # 기타 이벤트


class ScheduleMemberDto(BaseModel):
    """스케줄 멤버 DTO"""

    id: int | None = Field(default=None, serialization_alias="id")
    ko_name: str = Field(..., serialization_alias="koName", description="멤버 한글명")
    en_name: str = Field(..., serialization_alias="enName", description="멤버 영문명")
    artist_id: int | None = Field(
        None, serialization_alias="artistId", description="아티스트 ID"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ScheduleContentDto(BaseModel):
    """스케줄 콘텐츠 DTO"""

    id: int | None = Field(default=None, serialization_alias="id")
    type: str = Field(
        ..., serialization_alias="type", description="콘텐츠 유형 (video, image)"
    )
    path: str = Field(..., serialization_alias="path", description="콘텐츠 경로/URL")
    title: str | None = Field(
        None, serialization_alias="title", description="콘텐츠 제목"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ArtistScheduleDto(BaseModel):
    """아티스트 스케줄 DTO"""

    id: int = Field(serialization_alias="id")
    artist_id: int | None = Field(default=None, serialization_alias="artistId")
    unit_id: int | None = Field(default=None, serialization_alias="unitId")
    artist_ko_name: str = Field(serialization_alias="artistKoName")
    type: ScheduleTypeEnum = Field(serialization_alias="type")
    start_time: int = Field(
        ..., serialization_alias="startTime", description="일정 시작 시간 (밀리초)"
    )
    end_time: int = Field(
        ..., serialization_alias="endTime", description="일정 종료 시간 (밀리초)"
    )
    text: str | None = Field(default=None, serialization_alias="text")
    title: str = Field(serialization_alias="title")
    channel: str | None = Field(default=None, serialization_alias="channel")
    location: str | None = Field(default=None, serialization_alias="location")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    # 관계 데이터
    members: List[ScheduleMemberDto] = Field(
        default_factory=list, serialization_alias="members"
    )
    contents: List[ScheduleContentDto] = Field(
        default_factory=list, serialization_alias="contents"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ScheduleMemberCreateRequest(BaseModel):
    """스케줄 멤버 생성 요청"""

    ko_name: str = Field(..., description="멤버 한글명")
    en_name: str = Field(..., description="멤버 영문명")
    artist_id: int | None = Field(None, description="아티스트 ID")


class ScheduleContentCreateRequest(BaseModel):
    """스케줄 콘텐츠 생성 요청"""

    type: str = Field(..., description="콘텐츠 유형 (video, image)")
    path: str = Field(..., description="콘텐츠 경로/URL")
    title: str | None = Field(None, description="콘텐츠 제목")


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
