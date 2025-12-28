from pydantic import BaseModel, Field


class ArtistSimpleDto(BaseModel):
    unit_id: int = Field(alias="unitId")
    artist_id: int = Field(alias="artistId")
    name: str = Field()

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
