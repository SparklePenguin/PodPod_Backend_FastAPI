from typing import Optional
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime


class PodImageDto(BaseModel):
    """파티 이미지 DTO"""

    id: int = Field(alias="id", example=1)
    pod_id: int = Field(alias="podId", example=1)
    image_url: str = Field(alias="imageUrl", example="/uploads/pods/images/image.jpg")
    thumbnail_url: Optional[str] = Field(
        default=None, alias="thumbnailUrl", example="/uploads/pods/thumbnails/image.jpg"
    )
    display_order: int = Field(alias="displayOrder", example=0)
    created_at: Optional[datetime] = Field(
        default=None, alias="createdAt", example="2025-01-01T00:00:00"
    )

    @field_serializer("created_at")
    def serialize_created_at(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        return dt.isoformat() if isinstance(dt, datetime) else str(dt)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
