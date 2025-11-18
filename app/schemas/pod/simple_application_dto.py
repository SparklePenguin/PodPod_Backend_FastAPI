from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.schemas.follow import SimpleUserDto


class SimpleApplicationDto(BaseModel):
    id: int = Field(alias="id", description="신청서 ID")
    user: SimpleUserDto = Field(alias="user", description="신청한 사용자 정보")
    status: str = Field(
        alias="status", description="신청 상태 (PENDING, APPROVED, REJECTED)"
    )
    message: Optional[str] = Field(
        default=None, alias="message", description="신청 메시지"
    )
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
