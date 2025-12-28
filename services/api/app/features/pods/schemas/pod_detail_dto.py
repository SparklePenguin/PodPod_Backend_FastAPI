from pydantic import BaseModel, Field


class PodDetailDto(BaseModel):
    id: int = Field(serialization_alias="id", examples=[1])
    owner_id: int = Field(serialization_alias="ownerId", examples=[1])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
