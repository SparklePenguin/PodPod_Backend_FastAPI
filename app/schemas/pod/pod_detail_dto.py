from pydantic import BaseModel, Field


class PodDetailDto(BaseModel):
    id: int = Field(alias="id", example=1)
    owner_id: int = Field(alias="ownerId", example=1)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
