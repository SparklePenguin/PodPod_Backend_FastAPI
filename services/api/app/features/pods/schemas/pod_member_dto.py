from pydantic import BaseModel, Field

from app.features.follow.schemas import SimpleUserDto


class PodMemberDto(BaseModel):
    id: int = Field(serialization_alias="id", description="신청서 ID")
    user: SimpleUserDto = Field(serialization_alias="user")
    role: str = Field(serialization_alias="role")
    message: str | None = Field(
        default=None, serialization_alias="message", description="참여 신청 메시지"
    )
    joined_at: int = Field(
        serialization_alias="joinedAt", description="참여 신청 시간 (Unix timestamp)"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
