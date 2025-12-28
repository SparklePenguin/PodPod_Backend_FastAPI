from typing import List

from pydantic import BaseModel, Field


# - MARK: 동기화 응답
class ArtistsSyncDto(BaseModel):
    artist_created: int = Field(serialization_alias="artist_created")
    artist_updated: int = Field(serialization_alias="artist_updated")
    unit_created: int = Field(serialization_alias="unit_created")
    unit_updated: int = Field(serialization_alias="unit_updated")
    left_mvp_names: List[str] = Field(serialization_alias="left_mvp_names")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
