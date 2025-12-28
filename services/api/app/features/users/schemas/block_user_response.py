import datetime

from pydantic import BaseModel, Field


class BlockUserResponse(BaseModel):
    """사용자 차단 응답 스키마"""

    blocker_id: int = Field(
        ..., alias="blockerId", description="차단을 수행한 사용자 ID"
    )
    blocked_id: int = Field(..., alias="blockedId", description="차단당한 사용자 ID")
    created_at: datetime.datetime = Field(
        ..., alias="createdAt", description="차단 생성 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
