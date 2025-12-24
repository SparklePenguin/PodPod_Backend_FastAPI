"""
아티스트 관련 스키마
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# 아티스트 이미지 정보 응답
class ArtistImageDto(BaseModel):
    id: int = Field(serialization_alias="id", examples=[0])
    artist_id: int = Field(serialization_alias="artistId", examples=[0])
    path: Optional[str] = Field(
        default=None, serialization_alias="path", examples=[None]
    )
    file_id: Optional[str] = Field(
        default=None, serialization_alias="fileId", examples=[None]
    )
    is_animatable: bool = Field(
        default=False, serialization_alias="isAnimatable", examples=[False]
    )
    size: Optional[str] = Field(
        default=None, serialization_alias="size", examples=[None]
    )
    unit_id: Optional[int] = Field(serialization_alias="unitId", examples=[None])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# 아티스트 이미지 업데이트 요청
class UpdateArtistImageRequest(BaseModel):
    path: Optional[str] = Field(
        default=None, description="이미지 경로", serialization_alias="path"
    )
    file_id: Optional[str] = Field(
        default=None, description="파일 ID", serialization_alias="fileId"
    )
    is_animatable: Optional[bool] = Field(
        default=None,
        description="애니메이션 가능 여부",
        serialization_alias="isAnimatable",
    )
    size: Optional[str] = Field(
        default=None, description="이미지 크기", serialization_alias="size"
    )

    class Config:
        from_attributes = True
        populate_by_name = True


# 아티스트 이름 정보 응답
class ArtistNameDto(BaseModel):
    id: int = Field(serialization_alias="id", examples=[0])
    artist_id: int = Field(serialization_alias="artistId", examples=[0])
    code: str = Field(serialization_alias="code", examples=["string"])
    name: str = Field(serialization_alias="name", examples=["string"])
    unit_id: int = Field(serialization_alias="unitId", examples=[0])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


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


# 동기화 응답
class ArtistsSyncDto(BaseModel):
    artist_created: int = Field(serialization_alias="artist_created", examples=[0])
    artist_updated: int = Field(serialization_alias="artist_updated", examples=[0])
    unit_created: int = Field(serialization_alias="unit_created", examples=[0])
    unit_updated: int = Field(serialization_alias="unit_updated", examples=[0])
    left_mvp_names: List[str] = Field(
        serialization_alias="left_mvp_names", examples=[[]]
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
