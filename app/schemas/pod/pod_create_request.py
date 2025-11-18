from pydantic import BaseModel, Field, validator
from typing import Optional, List
import datetime
from app.models.pod.pod_enums import (
    AccompanySubCategory,
    GoodsSubCategory,
    TourSubCategory,
    EtcSubCategory,
)


class PodCreateRequest(BaseModel):
    title: str = Field(alias="title", example="string")
    description: Optional[str] = Field(
        default=None,
        alias="description",
        example="string?",
    )
    sub_categories: List[str] = Field(
        alias="subCategories",
        example=["string"],
    )
    capacity: int = Field(
        alias="capacity",
        example=4,
    )
    place: str = Field(
        alias="place",
        example="string",
    )
    address: str = Field(alias="address")
    sub_address: Optional[str] = Field(
        default=None, alias="subAddress", example="string?"
    )
    x: Optional[float] = Field(
        default=None, alias="x", example=127.123456, description="경도 (longitude)"
    )
    y: Optional[float] = Field(
        default=None, alias="y", example=37.123456, description="위도 (latitude)"
    )
    meetingDate: datetime.date = Field(
        alias="meetingDate",
        example="2025-01-01",
    )
    meetingTime: datetime.time = Field(
        alias="meetingTime",
        example="24:00",
    )
    selected_artist_id: Optional[int] = Field(
        default=None,
        alias="selectedArtistId",
        example=1,
    )

    @validator("sub_categories")
    def validate_sub_categories(cls, v):
        """서브 카테고리 검증"""
        if not v:
            raise ValueError("서브 카테고리는 필수입니다")

        # 모든 유효한 카테고리 키들을 수집
        valid_categories = set()
        valid_categories.update([cat.name for cat in AccompanySubCategory])
        valid_categories.update([cat.name for cat in GoodsSubCategory])
        valid_categories.update([cat.name for cat in TourSubCategory])
        valid_categories.update([cat.name for cat in EtcSubCategory])

        # 입력된 카테고리들이 유효한지 검증
        invalid_categories = []
        for category in v:
            if category not in valid_categories:
                invalid_categories.append(category)

        if invalid_categories:
            # 카테고리를 그룹별로 정리
            goods_categories = [cat.name for cat in GoodsSubCategory]
            accompany_categories = [cat.name for cat in AccompanySubCategory]
            tour_categories = [cat.name for cat in TourSubCategory]
            etc_categories = [cat.name for cat in EtcSubCategory]

            error_message = f"""유효하지 않은 카테고리입니다: {", ".join(invalid_categories)}

사용 가능한 카테고리:
📦 굿즈: {", ".join(goods_categories)}
👥 동행: {", ".join(accompany_categories)}
🗺️ 투어: {", ".join(tour_categories)}
📋 기타: {", ".join(etc_categories)}"""

            raise ValueError(error_message)

        return v

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
