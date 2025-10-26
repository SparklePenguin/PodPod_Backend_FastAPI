from typing import Optional
from pydantic import BaseModel, Field


class PodImageDto(BaseModel):
    """파티 이미지 DTO"""

    id: int = Field(alias="id", example=1)
    pod_id: int = Field(alias="podId", example=1)
    image_url: str = Field(alias="imageUrl", example="/uploads/pods/images/image.jpg")
    thumbnail_url: Optional[str] = Field(
        default=None, alias="thumbnailUrl", example="/uploads/pods/thumbnails/image.jpg"
    )
    display_order: int = Field(alias="displayOrder", example=0)
    created_at: Optional[str] = Field(
        default=None, alias="createdAt", example="2025-01-01T00:00:00"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
