from pydantic import BaseModel, Field


class ArtistNameDto(BaseModel):
    id: int = Field()
    artist_id: int = Field(alias="artistId")
    code: str = Field()
    name: str = Field()
    unit_id: int = Field(alias="unitId")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
