# 아티스트 간소화 정보 응답 (unitId, artistId, 이름)
from pydantic import BaseModel, Field


class ArtistDto(BaseModel):
    unit_id: int = Field(serialization_alias="unitId", examples=[0])
    artist_id: int = Field(serialization_alias="artistId", examples=[0])
    name: str = Field(serialization_alias="name", examples=["string"])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
