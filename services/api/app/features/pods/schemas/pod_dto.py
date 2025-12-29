from pydantic import BaseModel, Field


class PodDto(BaseModel):
    """간단한 파티 정보 DTO"""

    id: int = Field(..., description="파티 ID")
    owner_id: int = Field(..., alias="ownerId", description="파티장 ID")
    title: str = Field(..., description="파티 제목")
    thumbnail_url: str = Field(
        ..., alias="thumbnailUrl", description="파티 썸네일 이미지 URL"
    )
    sub_categories: list[str] = Field(
        ..., alias="subCategories", description="서브 카테고리 목록"
    )
    meeting_place: str = Field(..., alias="meetingPlace", description="만남 장소")
    meeting_date: int = Field(
        ..., alias="meetingDate", description="만남 날짜/시간 (timestamp)"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
