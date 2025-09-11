import datetime
import json
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class PodDto(BaseModel):
    id: int = Field(alias="id", example=1)
    owner_id: int = Field(alias="ownerId", example=1)
    title: str = Field(alias="title", example="string")
    description: Optional[str] = Field(
        default=None,
        alias="description",
        example="string?",
    )
    image_url: Optional[str] = Field(
        default=None,
        alias="imageUrl",
        example="string?",
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        alias="thumbnailUrl",
        example="string?",
    )
    sub_category: List[str] = Field(
        alias="sub_category",
        example=["string"],
    )
    capacity: int = Field(alias="capacity", example=4)
    place: str = Field(alias="place", example="string")
    address: str = Field(
        alias="address",
        example="string",
    )
    sub_address: Optional[str] = Field(
        default=None,
        alias="sub_address",
        example="string?",
    )
    meeting_date: datetime.date = Field(
        alias="meetingDate",
        example="2025-01-01",
    )
    meeting_time: datetime.time = Field(
        alias="meetingTime",
        example="24:00",
    )
    selected_artist_id: Optional[int] = Field(
        default=None,
        alias="selectedArtistId",
        example=1,
    )

    # 개인화 필드
    is_liked: bool = Field(default=False, alias="isLiked", example=False)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    @field_validator("sub_category", mode="before")
    @classmethod
    def parse_sub_category(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v
