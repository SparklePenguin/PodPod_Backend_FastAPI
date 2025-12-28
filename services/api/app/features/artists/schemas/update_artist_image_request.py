from pydantic import BaseModel, Field


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
