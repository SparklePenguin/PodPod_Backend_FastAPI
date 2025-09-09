from pydantic import BaseModel, Field


# 아티스트 이름 정보 응답
class ArtistNameDto(BaseModel):
    id: int = Field(alias="id", example=0)
    artist_id: int = Field(alias="artistId", example=0)
    code: str = Field(alias="code", example="string")
    name: str = Field(alias="name", example="string")
    unit_id: int = Field(alias="unitId", example=0)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
