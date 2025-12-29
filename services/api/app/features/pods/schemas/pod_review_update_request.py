from pydantic import BaseModel, Field


class PodReviewUpdateRequest(BaseModel):
    """후기 수정 요청 스키마"""

    rating: int = Field(..., ge=1, le=5, description="별점 (1-5)")
    content: str = Field(..., min_length=1, max_length=1000, description="후기 내용")
