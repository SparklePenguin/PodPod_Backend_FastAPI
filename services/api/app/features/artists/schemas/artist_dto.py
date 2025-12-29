from typing import List

from pydantic import BaseModel, Field

from .artist_image_dto import ArtistImageDto
from .artist_name_dto import ArtistNameDto


class ArtistDto(BaseModel):
    id: int = Field()
    name: str = Field()

    # BLIP API 관련 필드들
    unit_id: int | None = Field(default=None, alias="unitId")
    blip_artist_id: int | None = Field(default=None, alias="blipArtistId")

    # 관계 데이터 (리스트 그대로 노출)
    images: List[ArtistImageDto | None] = Field(default=None)
    names: List[ArtistNameDto | None] = Field(
        default=None,
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
