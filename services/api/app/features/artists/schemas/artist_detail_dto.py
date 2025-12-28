from typing import List

from pydantic import BaseModel, Field

from .artist_image import ArtistImageDto
from .artist_name import ArtistNameDto


# 아티스트 간소화 정보 응답 (unitId, artistId, 이름)
class ArtistSimpleDto(BaseModel):
    unit_id: int = Field(serialization_alias="unitId")
    artist_id: int = Field(serialization_alias="artistId")
    name: str = Field(serialization_alias="name")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# 아티스트 정보 응답
class ArtistDto(BaseModel):
    id: int = Field(serialization_alias="id")
    name: str = Field(serialization_alias="name")

    # BLIP API 관련 필드들
    unit_id: int | None = Field(default=None, serialization_alias="unitId")
    blip_artist_id: int | None = Field(default=None, serialization_alias="blipArtistId")

    # 관계 데이터 (리스트 그대로 노출)
    images: List[ArtistImageDto | None] = Field(
        default=None, serialization_alias="images"
    )
    names: List[ArtistNameDto | None] = Field(
        default=None,
        serialization_alias="names",
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# 아티스트 상세 정보 응답
class ArtistDetailDto(BaseModel):
    id: int = Field(serialization_alias="id")
    name: str = Field(serialization_alias="name")

    # BLIP API 관련 필드들
    unit_id: int | None = Field(default=None, serialization_alias="unitId")
    blip_artist_id: int | None = Field(default=None, serialization_alias="blipArtistId")

    # 관계 데이터 (리스트 그대로 노출)
    images: List[ArtistImageDto | None] = Field(
        default=None, serialization_alias="images"
    )
    names: List[ArtistNameDto | None] = Field(default=None, serialization_alias="names")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
