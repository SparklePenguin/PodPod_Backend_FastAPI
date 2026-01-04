"""아티스트 관련 스키마"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class ArtistImageDto(BaseModel):
    id: int = Field()
    artist_id: int = Field(alias="artistId")
    path: str | None = Field(default=None)
    file_id: str | None = Field(default=None, alias="fileId")
    is_animatable: bool = Field(default=False, alias="isAnimatable")
    size: str | None = Field(default=None)
    unit_id: int | None = Field(alias="unitId")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ArtistNameDto(BaseModel):
    id: int = Field()
    artist_id: int = Field(alias="artistId")
    code: str = Field()
    name: str = Field()
    unit_id: int = Field(alias="unitId")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


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


class ArtistDetailDto(BaseModel):
    id: int = Field()
    name: str = Field()

    # BLIP API 관련 필드들
    unit_id: int | None = Field(default=None, alias="unitId")
    blip_artist_id: int | None = Field(default=None, alias="blipArtistId")

    # 관계 데이터 (리스트 그대로 노출)
    images: List[ArtistImageDto | None] = Field(default=None)
    names: List[ArtistNameDto | None] = Field(default=None)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ArtistSimpleDto(BaseModel):
    unit_id: int = Field(alias="unitId")
    artist_id: int = Field(alias="artistId")
    name: str = Field()

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


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


class ArtistsSyncDto(BaseModel):
    artist_created: int = Field(alias="artist_created")
    artist_updated: int = Field(alias="artist_updated")
    unit_created: int = Field(alias="unit_created")
    unit_updated: int = Field(alias="unit_updated")
    left_mvp_names: List[str] = Field(alias="left_mvp_names")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class UpdateArtistImageRequest(BaseModel):
    path: str | None = Field(default=None, description="이미지 경로")
    file_id: str | None = Field(default=None, description="파일 ID", alias="fileId")
    is_animatable: bool | None = Field(
        default=None,
        description="애니메이션 가능 여부",
        alias="isAnimatable",
    )
    size: str | None = Field(default=None, description="이미지 크기")

    class Config:
        from_attributes = True
        populate_by_name = True
