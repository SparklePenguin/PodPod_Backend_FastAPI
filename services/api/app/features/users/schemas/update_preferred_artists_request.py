from typing import List

from pydantic import BaseModel, Field


class UpdatePreferredArtistsRequest(BaseModel):
    """선호 아티스트 요청"""

    artist_ids: List[int] = Field(default=[], alias="artistIds")

    model_config = {
        "populate_by_name": True,
    }
