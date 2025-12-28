from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class UserTendencyResultDto(BaseModel):
    """사용자 성향 테스트 결과 DTO"""

    id: int
    user_id: int = Field(..., alias="userId")
    tendency_type: str = Field(..., alias="tendencyType")
    answers: Dict[str, Any]
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}
