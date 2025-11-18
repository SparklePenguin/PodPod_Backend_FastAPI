from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.schemas.follow import SimpleUserDto


class PodApplicationDto(BaseModel):
    id: int = Field(alias="id", description="신청서 ID")
    podId: int = Field(alias="podId", description="파티 ID")
    user: SimpleUserDto = Field(alias="user", description="신청자 정보")
    message: Optional[str] = Field(
        default=None, alias="message", description="참여 신청 메시지"
    )
    status: str = Field(
        alias="status", description="신청 상태 (PENDING, APPROVED, REJECTED)"
    )
    appliedAt: int = Field(alias="appliedAt", description="신청 시간 (Unix timestamp)")
    reviewedAt: Optional[int] = Field(
        default=None, alias="reviewedAt", description="검토 시간 (Unix timestamp)"
    )
    reviewedBy: Optional[SimpleUserDto] = Field(
        default=None, alias="reviewedBy", description="검토자 정보"
    )

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
