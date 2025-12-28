from pydantic import BaseModel, Field


class PodReviewCreateRequest(BaseModel):
    """후기 생성 요청 스키마"""

    pod_id: int = Field(..., alias="podId", description="파티 ID")
    rating: int = Field(..., ge=1, le=5, description="별점 (1-5)")
    content: str = Field(..., min_length=1, max_length=1000, description="후기 내용")
