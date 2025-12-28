from pydantic import BaseModel, Field


class PodLikeDto(BaseModel):
    liked: bool = Field()
    count: int = Field()

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
