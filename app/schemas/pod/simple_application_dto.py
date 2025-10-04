from pydantic import BaseModel, Field
from typing import Optional


class SimpleApplicationDto(BaseModel):
    id: int = Field(alias="id", description="신청서 ID")
    status: str = Field(
        alias="status", description="신청 상태 (pending, approved, rejected)"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
