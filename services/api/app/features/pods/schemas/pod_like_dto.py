from pydantic import BaseModel, Field


class PodLikeDto(BaseModel):
    liked: bool = Field(serialization_alias="liked", examples=[True])
    count: int = Field(serialization_alias="count", examples=[0])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
