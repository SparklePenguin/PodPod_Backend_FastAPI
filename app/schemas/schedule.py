from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


#
class ArtistScheduleContnetDto(BaseModel):
    schedule_content_type: Optional[str] = Field(alias="scheduleContentType")
    schedule_content_path: Optional[str] = Field(alias="scheduleContentPath")
    schedule_content_title: Optional[str] = Field(alias="scheduleContentTitle")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ArtistScheduleDto(BaseModel):
    artist_id: int = Field(alias="artistId")
    schedule_type: int = Field(alias="scheduleType")
    schedule_start_time: datetime = Field(alias="scheduleStartTime")
    schedule_end_time: datetime = Field(alias="scheduleEndTime")
    schedule_text: Optional[str] = Field(default=None, alias="scheduleText")
    schedule_title: Optional[str] = Field(default=None, alias="scheduleTitle")
    schedule_members: List[int] = Field(default_factory=list, alias="scheduleMembers")
    schedule_contents: List[ArtistScheduleContnetDto] = Field(
        default_factory=list, alias="scheduleContents"
    )
    schedule_channel: Optional[str] = Field(default=None, alias="scheduleChannel")
    schedule_location: Optional[str] = Field(default=None, alias="scheduleLocation")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
