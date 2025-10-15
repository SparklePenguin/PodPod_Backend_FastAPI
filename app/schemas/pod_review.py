from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime, date, time
from app.schemas.follow import SimpleUserDto


class SimplePodDto(BaseModel):
    """간단한 파티 정보 DTO"""

    id: int = Field(..., alias="id", description="파티 ID", example=1)
    title: str = Field(
        ..., alias="title", description="파티 제목", example="아이돌 굿즈 구매"
    )
    image_url: Optional[str] = Field(
        None, alias="imageUrl", description="파티 이미지 URL"
    )
    sub_categories: list[str] = Field(
        ...,
        alias="subCategories",
        description="서브 카테고리 목록",
        example=["GROUP_PURCHASE"],
    )
    meeting_place: Optional[str] = Field(
        None, alias="meetingPlace", description="만남 장소", example="강남역"
    )
    meeting_date: Optional[int] = Field(
        None,
        alias="meetingDate",
        description="만남 날짜/시간 (timestamp)",
        example=1705276800000,
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }



class PodReviewCreateRequest(BaseModel):
    """후기 생성 요청 스키마"""

    pod_id: int = Field(..., alias="podId", description="파티 ID", example=1)
    rating: int = Field(..., ge=1, le=5, description="별점 (1-5)", example=5)
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="후기 내용",
        example="정말 좋은 파티였습니다!",
    )


class PodReviewUpdateRequest(BaseModel):
    """후기 수정 요청 스키마"""

    rating: int = Field(..., ge=1, le=5, description="별점 (1-5)", example=4)
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="후기 내용",
        example="수정된 후기 내용입니다.",
    )


class PodReviewDto(BaseModel):
    """후기 응답 DTO"""

    id: int = Field(..., description="후기 ID", example=1)
    pod: SimplePodDto = Field(..., description="파티 정보")
    user: SimpleUserDto = Field(..., description="작성자 정보")
    rating: int = Field(..., description="별점 (1-5)", example=5)
    content: str = Field(
        ..., description="후기 내용", example="정말 좋은 파티였습니다!"
    )
    created_at: datetime = Field(..., alias="createdAt", description="작성 시간")
    updated_at: datetime = Field(..., alias="updatedAt", description="수정 시간")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
