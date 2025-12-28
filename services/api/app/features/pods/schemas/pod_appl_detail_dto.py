from app.features.users.schemas import UserDto
from pydantic import BaseModel, Field, field_validator


class PodApplDetailDto(BaseModel):
    id: int = Field(description="신청서 ID")
    podId: int = Field(alias="podId", description="파티 ID")
    user: UserDto = Field(description="신청자 정보")
    message: str | None = Field(
        default=None, description="참여 신청 메시지"
    )
    status: str = Field(
        description="신청 상태 (PENDING, APPROVED, REJECTED)",
    )
    appliedAt: int = Field(alias="appliedAt", description="신청 시간 (Unix timestamp)")
    reviewedAt: int | None = Field(
        default=None,
        alias="reviewedAt",
        description="검토 시간 (Unix timestamp)",
    )
    reviewedBy: UserDto | None = Field(
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
