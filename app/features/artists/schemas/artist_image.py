from typing import Optional

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


# 아티스트 이미지 업데이트 요청 (기존 - JSON 데이터)
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
