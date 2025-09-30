from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ScheduleTypeEnum(int, Enum):
    """스케줄 유형 열거형"""

    GENERAL_CONTENT = 1  # 일반 콘텐츠 (영상, 방송 등)
    MUSIC_RELEASE = 2  # 음원/앨범 발매
    BIRTHDAY = 4  # 생일/기념일
    OTHER_EVENT = 5  # 기타 이벤트


class ScheduleMemberDto(BaseModel):
    """스케줄 멤버 DTO"""

    id: Optional[int] = None
    ko_name: str = Field(..., description="멤버 한글명")
    en_name: str = Field(..., description="멤버 영문명")
    artist_id: Optional[int] = Field(None, description="아티스트 ID")

    class Config:
        from_attributes = True


class ScheduleContentDto(BaseModel):
    """스케줄 콘텐츠 DTO"""

    id: Optional[int] = None
    type: str = Field(..., description="콘텐츠 유형 (video, image)")
    path: str = Field(..., description="콘텐츠 경로/URL")
    title: Optional[str] = Field(None, description="콘텐츠 제목")

    class Config:
        from_attributes = True


class ArtistScheduleDto(BaseModel):
    """아티스트 스케줄 DTO"""

    id: int
    artist_id: Optional[int] = None
    unit_id: Optional[int] = None
    artist_ko_name: str
    type: ScheduleTypeEnum
    start_time: int = Field(..., description="일정 시작 시간 (밀리초)")
    end_time: int = Field(..., description="일정 종료 시간 (밀리초)")
    text: Optional[str] = None
    title: str
    channel: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 관계 데이터
    members: List[ScheduleMemberDto] = []
    contents: List[ScheduleContentDto] = []

    class Config:
        from_attributes = True


class ScheduleMemberCreateRequest(BaseModel):
    """스케줄 멤버 생성 요청"""

    ko_name: str = Field(..., description="멤버 한글명")
    en_name: str = Field(..., description="멤버 영문명")
    artist_id: Optional[int] = Field(None, description="아티스트 ID")


class ScheduleContentCreateRequest(BaseModel):
    """스케줄 콘텐츠 생성 요청"""

    type: str = Field(..., description="콘텐츠 유형 (video, image)")
    path: str = Field(..., description="콘텐츠 경로/URL")
    title: Optional[str] = Field(None, description="콘텐츠 제목")


class ArtistScheduleCreateRequest(BaseModel):
    """아티스트 스케줄 생성 요청"""

    artist_id: Optional[int] = Field(None, description="아티스트 ID")
    unit_id: Optional[int] = Field(None, description="아티스트 유닛 ID")
    artist_ko_name: str = Field(..., description="아티스트 한글명")
    type: ScheduleTypeEnum = Field(..., description="일정 유형")
    start_time: int = Field(..., description="일정 시작 시간 (밀리초)")
    end_time: int = Field(..., description="일정 종료 시간 (밀리초)")
    text: Optional[str] = Field(None, description="일정 상세 설명")
    title: str = Field(..., description="일정 제목")
    channel: Optional[str] = Field(None, description="방송 채널")
    location: Optional[str] = Field(None, description="장소")

    # 관계 데이터
    members: List[ScheduleMemberCreateRequest] = []
    contents: List[ScheduleContentCreateRequest] = []
