from typing import List

from pydantic import BaseModel, Field


# - MARK: 동기화 응답
class ArtistsSyncDto(BaseModel):
    artist_created: int = Field(serialization_alias="artist_created", examples=[0])
    artist_updated: int = Field(serialization_alias="artist_updated", examples=[0])
    unit_created: int = Field(serialization_alias="unit_created", examples=[0])
    unit_updated: int = Field(serialization_alias="unit_updated", examples=[0])
    left_mvp_names: List[str] = Field(
        serialization_alias="left_mvp_names", examples=[[]]
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
