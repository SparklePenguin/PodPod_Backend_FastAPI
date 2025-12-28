from app.features.users.schemas import UserDto
from pydantic import BaseModel, Field


class PodMemberDto(BaseModel):
    id: int = Field(description="신청서 ID")
    user: UserDto = Field()
    role: str = Field()
    message: str | None = Field(default=None, description="참여 신청 메시지")
    joined_at: int = Field(
        alias="joinedAt", description="참여 신청 시간 (Unix timestamp)"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
