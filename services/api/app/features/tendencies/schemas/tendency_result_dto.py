from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class TendencyResultDto(BaseModel):
    """성향 테스트 결과 DTO"""

    id: int
    type: str
    description: str
    tendency_info: Dict[str, Any] = Field(..., alias="tendencyInfo")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}
