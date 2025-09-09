from typing import Optional
from pydantic import BaseModel, Field


# 아티스트 이미지 정보 응답
class ArtistImageDto(BaseModel):
    id: int = Field(alias="id", example=0)
    artist_id: int = Field(alias="artistId", example=0)
    path: Optional[str] = Field(default=None, alias="path", example=None)
    file_id: Optional[str] = Field(default=None, alias="fileId", example=None)
    is_animatable: bool = Field(default=False, alias="isAnimatable", example=False)
    size: Optional[str] = Field(default=None, alias="size", example=None)
    unit_id: Optional[int] = Field(alias="unitId", example=None)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
