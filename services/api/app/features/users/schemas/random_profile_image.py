"""
랜덤 프로필 이미지 관련 스키마
"""

from pydantic import BaseModel, Field


class RandomProfileImageDto(BaseModel):
    """랜덤 프로필 이미지 응답 DTO"""

    image_url: str = Field(
        ...,
        alias="imageUrl",
        description="랜덤으로 선택된 프로필 이미지 URL",
    )
    image_name: str = Field(..., alias="imageName", description="이미지 파일명")

    model_config = {"from_attributes": True, "populate_by_name": True}
