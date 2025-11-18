from pydantic import BaseModel, Field


class PodLikeDto(BaseModel):
    liked: bool = Field(alias="liked", example=True)
    count: int = Field(alias="count", example=0)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
