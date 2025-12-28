from pydantic import BaseModel, Field


class PodLikeDto(BaseModel):
    liked: bool = Field(serialization_alias="liked")
    count: int = Field(serialization_alias="count")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
