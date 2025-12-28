from pydantic import BaseModel, Field


class ArtistImageDto(BaseModel):
    id: int = Field()
    artist_id: int = Field(alias="artistId")
    path: str | None = Field(default=None)
    file_id: str | None = Field(default=None, alias="fileId")
    is_animatable: bool = Field(default=False, alias="isAnimatable")
    size: str | None = Field(default=None)
    unit_id: int | None = Field(alias="unitId")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
