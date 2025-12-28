from typing import List, Optional

from pydantic import BaseModel, Field

from .artist_image import ArtistImageDto
from .artist_name import ArtistNameDto


# 아티스트 간소화 정보 응답 (unitId, artistId, 이름)
class ArtistSimpleDto(BaseModel):
    unit_id: int = Field(serialization_alias="unitId", examples=[0])
    artist_id: int = Field(serialization_alias="artistId", examples=[0])
    name: str = Field(serialization_alias="name", examples=["string"])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# 아티스트 정보 응답
class ArtistDto(BaseModel):
    id: int = Field(serialization_alias="id", examples=[0])
    name: str = Field(serialization_alias="name", examples=["string"])

    # BLIP API 관련 필드들
    unit_id: Optional[int] = Field(
        default=None, serialization_alias="unitId", examples=[None]
    )
    blip_artist_id: Optional[int] = Field(
        default=None, serialization_alias="blipArtistId", examples=[None]
    )

    # 관계 데이터 (리스트 그대로 노출)
    images: Optional[List[ArtistImageDto]] = Field(
        default=None, serialization_alias="images", examples=[None]
    )
    names: Optional[List[ArtistNameDto]] = Field(
        default=None, serialization_alias="names", examples=[None]
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# 아티스트 상세 정보 응답
class ArtistDetailDto(BaseModel):
    id: int = Field(serialization_alias="id", examples=[0])
    name: str = Field(serialization_alias="name", examples=["string"])

    # BLIP API 관련 필드들
    unit_id: Optional[int] = Field(
        default=None, serialization_alias="unitId", examples=[None]
    )
    blip_artist_id: Optional[int] = Field(
        default=None, serialization_alias="blipArtistId", examples=[None]
    )

    # 관계 데이터 (리스트 그대로 노출)
    images: Optional[List[ArtistImageDto]] = Field(
        default=None, serialization_alias="images", examples=[None]
    )
    names: Optional[List[ArtistNameDto]] = Field(
        default=None, serialization_alias="names", examples=[None]
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
