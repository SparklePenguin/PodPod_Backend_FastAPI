from pydantic import BaseModel, Field, field_validator

from app.features.follow.schemas import SimpleUserDto


class PodApplicationDto(BaseModel):
    id: int = Field(serialization_alias="id", description="신청서 ID")
    podId: int = Field(serialization_alias="podId", description="파티 ID")
    user: SimpleUserDto = Field(serialization_alias="user", description="신청자 정보")
    message: str | None = Field(
        default=None, serialization_alias="message", description="참여 신청 메시지"
    )
    status: str = Field(
        serialization_alias="status",
        description="신청 상태 (PENDING, APPROVED, REJECTED)",
    )
    appliedAt: int = Field(
        serialization_alias="appliedAt", description="신청 시간 (Unix timestamp)"
    )
    reviewedAt: int | None = Field(
        default=None,
        serialization_alias="reviewedAt",
        description="검토 시간 (Unix timestamp)",
    )
    reviewedBy: SimpleUserDto | None = Field(
        default=None, serialization_alias="reviewedBy", description="검토자 정보"
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
