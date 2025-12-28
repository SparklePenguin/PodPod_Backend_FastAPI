from pydantic import BaseModel, Field


# 아티스트 이미지 정보 응답
class ArtistImageDto(BaseModel):
    id: int = Field(serialization_alias="id")
    artist_id: int = Field(serialization_alias="artistId")
    path: str | None = Field(default=None, serialization_alias="path")
    file_id: str | None = Field(default=None, serialization_alias="fileId")
    is_animatable: bool = Field(default=False, serialization_alias="isAnimatable")
    size: str | None = Field(default=None, serialization_alias="size")
    unit_id: int | None = Field(serialization_alias="unitId")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# 아티스트 이미지 업데이트 요청 (기존 - JSON 데이터)
class UpdateArtistImageRequest(BaseModel):
    path: str | None = Field(
        default=None, description="이미지 경로", serialization_alias="path"
    )
    file_id: str | None = Field(
        default=None, description="파일 ID", serialization_alias="fileId"
    )
    is_animatable: bool | None = Field(
        default=None,
        description="애니메이션 가능 여부",
        serialization_alias="isAnimatable",
    )
    size: str | None = Field(
        default=None, description="이미지 크기", serialization_alias="size"
    )

    class Config:
        from_attributes = True
        populate_by_name = True
