import datetime
from typing import List

from app.features.pods.models.pod.pod_enums import (
    AccompanySubCategory,
    EtcSubCategory,
    GoodsSubCategory,
    TourSubCategory,
)
from pydantic import BaseModel, Field, field_validator


class PodCreateRequest(BaseModel):
    title: str = Field()
    description: str | None = Field(default=None)
    sub_categories: List[str] = Field(alias="subCategories")
    capacity: int = Field()
    place: str = Field()
    address: str = Field()
    sub_address: str | None = Field(default=None, alias="subAddress")
    x: float | None = Field(default=None, description="경도 (longitude)")
    y: float | None = Field(default=None, description="위도 (latitude)")
    meetingDate: datetime.date = Field(alias="meetingDate")
    meetingTime: datetime.time = Field(alias="meetingTime")
    selected_artist_id: int | None = Field(default=None, alias="selectedArtistId")

    @field_validator("sub_categories")
    @classmethod
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
