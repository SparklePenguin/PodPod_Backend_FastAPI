from datetime import datetime
from typing import List

from app.features.artists.schemas.artist_name_schemas import ArtistNameDto
from pydantic import BaseModel, Field

from app.features.artists.schemas.artist_image import ArtistImageDto
from app.features.artists.schemas.artist_schemas import ArtistDto


# 아티스트 유닛 정보 응답
class ArtistUnitDto(BaseModel):
    id: int = Field(serialization_alias="id", examples=[0])
    name: str = Field(serialization_alias="name", examples=["string"])
    artist_id: int = Field(serialization_alias="artistId", examples=[0])
    type: str = Field(serialization_alias="type", examples=["string"])
    is_active: bool = Field(serialization_alias="isActive", examples=[True])
    created_at: datetime = Field(
        serialization_alias="createdAt", examples=[datetime.now()]
    )
    updated_at: datetime = Field(
        serialization_alias="updatedAt", examples=[datetime.now()]
    )
    # 관계 데이터
    names: List[ArtistNameDto] = Field(serialization_alias="names", examples=[[]])
    images: List[ArtistImageDto] = Field(serialization_alias="images", examples=[[]])
    members: List[ArtistDto] = Field(serialization_alias="members", examples=[[]])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }
