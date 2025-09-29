from typing import Optional, List
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


# 아티스트 이미지 업데이트 요청 (기존 - JSON 데이터)
class UpdateArtistImageRequest(BaseModel):
    path: Optional[str] = Field(default=None, description="이미지 경로", alias="path")
    file_id: Optional[str] = Field(default=None, description="파일 ID", alias="fileId")
    is_animatable: Optional[bool] = Field(
        default=None, description="애니메이션 가능 여부", alias="isAnimatable"
    )
    size: Optional[str] = Field(default=None, description="이미지 크기", alias="size")

    class Config:
        from_attributes = True
        populate_by_name = True
