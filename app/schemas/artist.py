# - MARK: 아티스트 정보 응답
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# - MARK: 아티스트 정보 응답
class ArtistDto(BaseModel):
    id: int = Field(alias="id")  # 필수값
    type: Optional[str] = Field(default=None, alias="type")
    name: str = Field(alias="name")  # 필수값
    profile_image: Optional[str] = Field(default=None, alias="profileImage")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": lambda x: (
            x.replace("_", "").lower()
            if x.startswith("_")
            else x.replace("_", "").lower()
        ),
    }
