from typing import List
from pydantic import BaseModel, Field


# - MARK: 동기화 응답
class ArtistsSyncDto(BaseModel):
    artist_created: int = Field(alias="artist_created", example=0)
    artist_updated: int = Field(alias="artist_updated", example=0)
    unit_created: int = Field(alias="unit_created", example=0)
    unit_updated: int = Field(alias="unit_updated", example=0)
    left_mvp_names: List[str] = Field(alias="left_mvp_names", example=[])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
