import datetime
import json
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from app.models.pod.pod_enums import (
    AccompanySubCategory,
    GoodsSubCategory,
    TourSubCategory,
    EtcSubCategory,
)
from app.models.pod.pod_status import PodStatus


class PodDto(BaseModel):
    id: int = Field(alias="id", example=1)
    owner_id: int = Field(alias="ownerId", example=1)
    title: str = Field(alias="title", example="string")
    description: Optional[str] = Field(
        default=None,
        alias="description",
        example="string?",
    )
    image_url: Optional[str] = Field(
        default=None,
        alias="imageUrl",
        example="string?",
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        alias="thumbnailUrl",
        example="string?",
    )
    sub_categories: List[str] = Field(
        alias="subCategories",
        example=["string"],
    )
    capacity: int = Field(alias="capacity", example=4)
    place: str = Field(alias="place", example="string")
    address: str = Field(
        alias="address",
        example="string",
    )
    sub_address: Optional[str] = Field(
        default=None,
        alias="subAddress",
        example="string?",
    )
    meeting_date: datetime.date = Field(
        alias="meetingDate",
        example="2025-01-01",
    )
    meeting_time: datetime.time = Field(
        alias="meetingTime",
        example="24:00",
    )
    selected_artist_id: Optional[int] = Field(
        default=None,
        alias="selectedArtistId",
        example=1,
    )
    status: PodStatus = Field(
        default=PodStatus.RECRUITING,
        alias="status",
        example="RECRUITING",
        description="파티 상태 (RECRUITING: 모집중, FULL: 인원 가득참, COMPLETED: 모집 완료, CLOSED: 종료)",
    )

    # 개인화 필드
    is_liked: bool = Field(default=False, alias="isLiked", example=False)

    # 통계 및 메타데이터 필드
    view_count: int = Field(default=0, alias="viewCount", example=0)
    joined_users_count: int = Field(default=0, alias="joinedUsersCount", example=0)
    created_at: datetime.datetime = Field(
        alias="createdAt", example="2025-01-01T00:00:00"
    )
    updated_at: datetime.datetime = Field(
        alias="updatedAt", example="2025-01-01T00:00:00"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    @field_validator("sub_categories", mode="before")
    @classmethod
    def parse_sub_categories(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v

    @field_validator("sub_categories")
    @classmethod
    def validate_sub_categories(cls, v: List[str]) -> List[str]:
        """서브 카테고리 검증 및 필터링"""
        if not v:
            return []

        # 모든 유효한 카테고리 키들을 수집
        valid_categories = set()
        valid_categories.update([cat.name for cat in AccompanySubCategory])
        valid_categories.update([cat.name for cat in GoodsSubCategory])
        valid_categories.update([cat.name for cat in TourSubCategory])
        valid_categories.update([cat.name for cat in EtcSubCategory])

        # 유효한 카테고리만 필터링
        valid_sub_categories = [cat for cat in v if cat in valid_categories]

        # 유효하지 않은 카테고리가 있으면 로그만 남기고 필터링된 결과 반환
        invalid_categories = [cat for cat in v if cat not in valid_categories]
        if invalid_categories:
            # 카테고리를 그룹별로 정리
            goods_categories = [cat.name for cat in GoodsSubCategory]
            accompany_categories = [cat.name for cat in AccompanySubCategory]
            tour_categories = [cat.name for cat in TourSubCategory]
            etc_categories = [cat.name for cat in EtcSubCategory]

            print(
                f"""⚠️ 유효하지 않은 카테고리가 필터링되었습니다: {", ".join(invalid_categories)}

사용 가능한 카테고리:
📦 굿즈: {", ".join(goods_categories)}
👥 동행: {", ".join(accompany_categories)}
🗺️ 투어: {", ".join(tour_categories)}
📋 기타: {", ".join(etc_categories)}"""
            )

        return valid_sub_categories
