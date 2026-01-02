"""Review 관련 스키마들"""

from datetime import datetime, timezone

from app.features.pods.schemas.pod_schemas import PodDto
from app.features.users.schemas import UserDto
from pydantic import BaseModel, Field, field_serializer


# - MARK: Pod Review DTO
class PodReviewDto(BaseModel):
    """후기 응답 DTO"""

    id: int = Field(..., description="후기 ID")
    pod: PodDto = Field(..., description="파티 정보")
    user: UserDto = Field(..., description="작성자 정보")
    rating: int = Field(..., description="별점 (1-5)")
    content: str = Field(..., description="후기 내용")
    created_at: datetime = Field(..., alias="createdAt", description="작성 시간")
    updated_at: datetime = Field(..., alias="updatedAt", description="수정 시간")

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime) -> str:
        """datetime을 ISO format (Z 포함)으로 변환"""
        if dt is None:
            return None
        # timezone 정보가 없으면 UTC로 추가
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Pod Review Create Request
class PodReviewCreateRequest(BaseModel):
    """후기 생성 요청 스키마"""

    pod_id: int = Field(..., alias="podId", description="파티 ID")
    rating: int = Field(..., ge=1, le=5, description="별점 (1-5)")
    content: str = Field(..., min_length=1, max_length=1000, description="후기 내용")


# - MARK: Pod Review Update Request
class PodReviewUpdateRequest(BaseModel):
    """후기 수정 요청 스키마"""

    rating: int = Field(..., ge=1, le=5, description="별점 (1-5)")
    content: str = Field(..., min_length=1, max_length=1000, description="후기 내용")
