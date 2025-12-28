from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer


class PodImageDto(BaseModel):
    """파티 이미지 DTO"""

    id: int = Field(serialization_alias="id", examples=[1])
    pod_id: int = Field(serialization_alias="podId", examples=[1])
    image_url: str = Field(
        serialization_alias="imageUrl", examples=["/uploads/pods/images/image.jpg"]
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        serialization_alias="thumbnailUrl",
        examples=["/uploads/pods/thumbnails/image.jpg"],
    )
    display_order: int = Field(serialization_alias="displayOrder", examples=[0])
    created_at: Optional[datetime] = Field(
        default=None, serialization_alias="createdAt", examples=["2025-01-01T00:00:00"]
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
