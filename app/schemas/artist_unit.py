from app.schemas.artist import ArtistDto
from app.schemas.artist_image import ArtistImageDto
from app.schemas.artist_name import ArtistNameDto
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime


# 아티스트 유닛 정보 응답
class ArtistUnitDto(BaseModel):
    id: int = Field(alias="id", example=0)
    name: str = Field(alias="name", example="string")
    artist_id: int = Field(alias="artistId", example=0)
    type: str = Field(alias="type", example="string")
    is_active: bool = Field(alias="isActive", example=True)
    created_at: datetime = Field(alias="createdAt", example=datetime.now())
    updated_at: datetime = Field(alias="updatedAt", example=datetime.now())
    # 관계 데이터
    names: List[ArtistNameDto] = Field(alias="names", example=[])
    images: List[ArtistImageDto] = Field(alias="images", example=[])
    members: List[ArtistDto] = Field(alias="members", example=[])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }
