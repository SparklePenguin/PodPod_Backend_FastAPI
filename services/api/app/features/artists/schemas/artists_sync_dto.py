from typing import List

from pydantic import BaseModel, Field


class ArtistsSyncDto(BaseModel):
    artist_created: int = Field(alias="artist_created")
    artist_updated: int = Field(alias="artist_updated")
    unit_created: int = Field(alias="unit_created")
    unit_updated: int = Field(alias="unit_updated")
    left_mvp_names: List[str] = Field(alias="left_mvp_names")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
