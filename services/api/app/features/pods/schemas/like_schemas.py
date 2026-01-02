"""Like 관련 스키마들"""

from pydantic import BaseModel, Field


# - MARK: Pod Like DTO
class PodLikeDto(BaseModel):
    liked: bool = Field()
    count: int = Field()

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
