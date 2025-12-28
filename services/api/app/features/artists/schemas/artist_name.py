from pydantic import BaseModel, Field


# 아티스트 이름 정보 응답
class ArtistNameDto(BaseModel):
    id: int = Field(serialization_alias="id", examples=[0])
    artist_id: int = Field(serialization_alias="artistId", examples=[0])
    code: str = Field(serialization_alias="code", examples=["string"])
    name: str = Field(serialization_alias="name", examples=["string"])
    unit_id: int = Field(serialization_alias="unitId", examples=[0])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
