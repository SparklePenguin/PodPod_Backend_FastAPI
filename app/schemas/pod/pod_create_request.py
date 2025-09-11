from pydantic import BaseModel, Field
from typing import Optional, List
import datetime


class PodCreateRequest(BaseModel):
    title: str = Field(alias="title", example="string")
    description: Optional[str] = Field(
        default=None,
        alias="description",
        example="string?",
    )
    sub_category: List[str] = Field(
        alias="subCategory",
        example=["string"],
    )
    capacity: int = Field(
        alias="capacity",
        example=4,
    )
    place: str = Field(
        alias="place",
        example="string",
    )
    address: str = Field(alias="address")
    sub_address: Optional[str] = Field(
        default=None, alias="subAddress", example="string?"
    )
    meetingDate: datetime.date = Field(
        alias="meetingDate",
        example="2025-01-01",
    )
    meetingTime: datetime.time = Field(
        alias="meetingTime",
        example="24:00",
    )
    selected_artist_id: Optional[int] = Field(
        default=None,
        alias="selectedArtistId",
        example=1,
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
