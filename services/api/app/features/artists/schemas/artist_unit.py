from datetime import datetime
from typing import List

from app.features.artists.schemas.artist_detail_dto import ArtistDto
from app.features.artists.schemas.artist_image import ArtistImageDto
from app.features.artists.schemas.artist_name import ArtistNameDto
from pydantic import BaseModel, Field


# 아티스트 유닛 정보 응답
class ArtistUnitDto(BaseModel):
    id: int = Field(serialization_alias="id")
    name: str = Field(serialization_alias="name")
    artist_id: int = Field(serialization_alias="artistId")
    type: str = Field(serialization_alias="type")
    is_active: bool = Field(serialization_alias="isActive")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    # 관계 데이터
    names: List[ArtistNameDto] = Field(serialization_alias="names")
    images: List[ArtistImageDto] = Field(serialization_alias="images")
    members: List[ArtistDto] = Field(serialization_alias="members")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }
