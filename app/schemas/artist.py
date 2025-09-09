from typing import Optional, List

from pydantic import BaseModel, Field
from .artist_image import ArtistImageDto
from .artist_name import ArtistNameDto


# 아티스트 정보 응답
class ArtistDto(BaseModel):
    id: int = Field(alias="id", example=0)
    name: str = Field(alias="name", example="string")

    # BLIP API 관련 필드들
    unit_id: Optional[int] = Field(default=None, alias="unitId", example=None)
    blip_artist_id: Optional[int] = Field(
        default=None, alias="blipArtistId", example=None
    )

    # 관계 데이터 (리스트 그대로 노출)
    images: Optional[List[ArtistImageDto]] = Field(
        default=None, alias="images", example=None
    )
    names: Optional[List[ArtistNameDto]] = Field(
        default=None, alias="names", example=None
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
