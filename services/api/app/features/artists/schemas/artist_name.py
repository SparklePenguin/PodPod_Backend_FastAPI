from pydantic import BaseModel, Field


# 아티스트 이름 정보 응답
class ArtistNameDto(BaseModel):
    id: int = Field(serialization_alias="id")
    artist_id: int = Field(serialization_alias="artistId")
    code: str = Field(serialization_alias="code")
    name: str = Field(serialization_alias="name")
    unit_id: int = Field(serialization_alias="unitId")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
