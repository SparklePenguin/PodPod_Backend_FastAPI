from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class PodImageDto(BaseModel):
    """파티 이미지 DTO"""

    id: int = Field(serialization_alias="id")
    pod_id: int = Field(serialization_alias="podId")
    image_url: str = Field(serialization_alias="imageUrl")
    thumbnail_url: str | None = Field(default=None, serialization_alias="thumbnailUrl")
    display_order: int = Field(serialization_alias="displayOrder")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat() if isinstance(dt, datetime) else str(dt)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
