from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_serializer

from app.features.follow.schemas.follow import SimpleUserDto


class SimplePodDto(BaseModel):
    """간단한 파티 정보 DTO"""

    id: int = Field(..., serialization_alias="id", description="파티 ID", examples=[1])
    owner_id: int = Field(
        ..., serialization_alias="ownerId", description="파티장 ID", examples=[1]
    )
    title: str = Field(
        ...,
        serialization_alias="title",
        description="파티 제목",
        examples=["아이돌 굿즈 구매"],
    )
    thumbnail_url: str = Field(
        ..., serialization_alias="thumbnailUrl", description="파티 썸네일 이미지 URL"
    )
    sub_categories: list[str] = Field(
        ...,
        serialization_alias="subCategories",
        description="서브 카테고리 목록",
        examples=[["GROUP_PURCHASE"]],
    )
    meeting_place: str = Field(
        ...,
        serialization_alias="meetingPlace",
        description="만남 장소",
        examples=["강남역"],
    )
    meeting_date: int = Field(
        ...,
        serialization_alias="meetingDate",
        description="만남 날짜/시간 (timestamp)",
        examples=[1705276800000],
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PodReviewCreateRequest(BaseModel):
    """후기 생성 요청 스키마"""

    pod_id: int = Field(
        ..., serialization_alias="podId", description="파티 ID", examples=[1]
    )
    rating: int = Field(..., ge=1, le=5, description="별점 (1-5)", examples=[5])
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="후기 내용",
        examples=["정말 좋은 파티였습니다!"],
    )


class PodReviewUpdateRequest(BaseModel):
    """후기 수정 요청 스키마"""

    rating: int = Field(..., ge=1, le=5, description="별점 (1-5)", examples=[4])
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="후기 내용",
        examples=["수정된 후기 내용입니다."],
    )


class PodReviewDto(BaseModel):
    """후기 응답 DTO"""

    id: int = Field(..., description="후기 ID", examples=[1])
    pod: SimplePodDto = Field(..., description="파티 정보")
    user: SimpleUserDto = Field(..., description="작성자 정보")
    rating: int = Field(..., description="별점 (1-5)", examples=[5])
    content: str = Field(
        ..., description="후기 내용", examples=["정말 좋은 파티였습니다!"]
    )
    created_at: datetime = Field(
        ..., serialization_alias="createdAt", description="작성 시간"
    )
    updated_at: datetime = Field(
        ..., serialization_alias="updatedAt", description="수정 시간"
    )

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
