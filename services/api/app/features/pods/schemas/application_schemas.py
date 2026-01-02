"""Application 관련 스키마들"""

from datetime import datetime

from app.features.users.schemas import UserDto
from pydantic import BaseModel, Field


# - MARK: Pod Application DTO
class PodApplDto(BaseModel):
    id: int = Field(description="신청서 ID")
    user: UserDto = Field(description="신청한 사용자 정보")
    status: str = Field(
        description="신청 상태 (pending, approved, rejected)",
    )
    message: str | None = Field(default=None, description="신청 메시지")
    applied_at: datetime = Field(alias="appliedAt", description="신청 시간")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Pod Application Detail DTO
class PodApplDetailDto(BaseModel):
    id: int = Field(description="신청서 ID")
    podId: int = Field(alias="podId", description="파티 ID")
    user: UserDto = Field(description="신청자 정보")
    message: str | None = Field(default=None, description="참여 신청 메시지")
    status: str = Field(
        description="신청 상태 (pending, approved, rejected)",
    )
    appliedAt: datetime = Field(alias="appliedAt", description="신청 시간")
    reviewedAt: datetime | None = Field(
        default=None,
        alias="reviewedAt",
        description="검토 시간",
    )
    reviewedBy: UserDto | None = Field(
        default=None, alias="reviewedBy", description="검토자 정보"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Apply To Pod Request
class ApplyToPodRequest(BaseModel):
    """파티 참여 신청 요청"""

    message: str | None = Field(default=None, description="참여 신청 메시지")

    model_config = {"populate_by_name": True}


# - MARK: Review Application Request
class ReviewApplicationRequest(BaseModel):
    """신청서 승인/거절 요청"""

    status: str = Field(description="승인 상태 (approved, rejected)")

    model_config = {"populate_by_name": True}
