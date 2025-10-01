from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.follow import SimpleUserDto


class PodMemberDto(BaseModel):
    id: int = Field(alias="id", description="신청서 ID")
    user: SimpleUserDto = Field(alias="user")
    role: str = Field(alias="role")
    message: Optional[str] = Field(
        default=None, alias="message", description="참여 신청 메시지"
    )
    created_at: int = Field(
        alias="createdAt", description="참여 신청 시간 (Unix timestamp)"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
