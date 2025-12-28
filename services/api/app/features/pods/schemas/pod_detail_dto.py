from pydantic import BaseModel, Field


class PodDetailDto(BaseModel):
    id: int = Field(serialization_alias="id")
    owner_id: int = Field(serialization_alias="ownerId")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
