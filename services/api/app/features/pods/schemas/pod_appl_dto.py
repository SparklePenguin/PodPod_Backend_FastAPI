from app.features.users.schemas import UserDto
from pydantic import BaseModel, Field, field_validator


class PodApplDto(BaseModel):
    id: int = Field(description="신청서 ID")
    user: UserDto = Field(description="신청한 사용자 정보")
    status: str = Field(
        description="신청 상태 (PENDING, APPROVED, REJECTED)",
    )
    message: str | None = Field(default=None, description="신청 메시지")
    applied_at: int = Field(alias="appliedAt", description="신청 시간 (Unix timestamp)")

    @field_validator("status", mode="before")
    @classmethod
    def uppercase_status(cls, v: str) -> str:
        """status를 대문자로 변환"""
        if v:
            return v.upper()
        return v

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
