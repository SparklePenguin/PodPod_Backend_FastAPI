from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from .artist_dto import ArtistDto
from .artist_image_dto import ArtistImageDto
from .artist_name_dto import ArtistNameDto


class ArtistUnitDto(BaseModel):
    id: int = Field()
    name: str = Field()
    artist_id: int = Field(alias="artistId")
    type: str = Field()
    is_active: bool = Field(alias="isActive")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    # 관계 데이터
    names: List[ArtistNameDto] = Field()
    images: List[ArtistImageDto] = Field()
    members: List[ArtistDto] = Field()

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }
