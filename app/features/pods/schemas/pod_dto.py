import datetime
import json

# 순환 import 방지를 위한 TYPE_CHECKING
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.features.follow.schemas import SimpleUserDto
from app.features.pods.models.pod.pod_enums import (
    AccompanySubCategory,
    EtcSubCategory,
    GoodsSubCategory,
    TourSubCategory,
)
from app.features.pods.models.pod.pod_status import PodStatus
from app.features.pods.schemas.pod_image_dto import PodImageDto
from app.features.pods.schemas.simple_application_dto import SimpleApplicationDto

if TYPE_CHECKING:
    from app.features.pods.schemas import PodReviewDto


class PodSearchRequest(BaseModel):
    """팟 검색 요청"""

    title: Optional[str] = Field(
        None, serialization_alias="title", description="팟 제목"
    )
    main_category: Optional[str] = Field(
        None,
        serialization_alias="mainCategory",
        description="메인 카테고리 (ACCOMPANY, GOODS, TOUR, ETC)",
    )
    sub_category: Optional[str] = Field(
        None, serialization_alias="subCategory", description="서브 카테고리"
    )
    start_date: Optional[datetime.date] = Field(
        None, serialization_alias="startDate", description="시작 날짜"
    )
    end_date: Optional[datetime.date] = Field(
        None, serialization_alias="endDate", description="종료 날짜"
    )
    location: Optional[List[str]] = Field(
        None,
        serialization_alias="location",
        description="지역 리스트 (address 또는 sub_address에 포함)",
    )
    page: Optional[int] = Field(
        1, serialization_alias="page", ge=1, description="페이지 번호"
    )
    page_size: Optional[int] = Field(
        20, serialization_alias="pageSize", ge=1, le=100, description="페이지 크기"
    )
    limit: Optional[int] = Field(
        None,
        serialization_alias="limit",
        description="결과 제한 (deprecated, pageSize 사용 권장)",
    )

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, values):
        """null 값을 기본값으로 변경"""
        if isinstance(values, dict):
            if values.get("page") is None:
                values["page"] = 1
            if values.get("pageSize") is None:
                values["pageSize"] = 20
        return values

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PodDto(BaseModel):
    id: int = Field(serialization_alias="id", examples=[1])
    owner_id: int = Field(serialization_alias="ownerId", examples=[1])
    title: str = Field(serialization_alias="title", examples=["string"])
    description: str = Field(
        serialization_alias="description",
        examples=["파티 설명"],
    )
    image_url: Optional[str] = Field(
        default=None,
        serialization_alias="imageUrl",
        examples=["string?"],
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        serialization_alias="thumbnailUrl",
        examples=["string?"],
    )
    sub_categories: List[str] = Field(
        serialization_alias="subCategories",
        examples=[["string"]],
    )
    capacity: int = Field(serialization_alias="capacity", examples=[4])
    place: str = Field(serialization_alias="meetingPlace", examples=["string"])
    address: str = Field(
        serialization_alias="address",
        examples=["string"],
    )
    sub_address: Optional[str] = Field(
        default=None,
        serialization_alias="subAddress",
        examples=["string?"],
    )
    x: Optional[float] = Field(
        default=None,
        serialization_alias="x",
        examples=[127.123456],
        description="경도 (longitude)",
    )
    y: Optional[float] = Field(
        default=None,
        serialization_alias="y",
        examples=[37.123456],
        description="위도 (latitude)",
    )
    meeting_date: Optional[int] = Field(
        serialization_alias="meetingDate",
        examples=[1705276800000],
        description="만남 날짜/시간 (timestamp in milliseconds)",
    )
    selected_artist_id: Optional[int] = Field(
        default=None,
        serialization_alias="selectedArtistId",
        examples=[1],
    )
    status: PodStatus = Field(
        default=PodStatus.RECRUITING,
        serialization_alias="status",
        examples=["RECRUITING"],
        description="파티 상태 (RECRUITING: 모집중, FULL: 인원 가득참, COMPLETED: 모집 완료, CLOSED: 종료)",
    )
    chat_channel_url: Optional[str] = Field(
        default=None,
        serialization_alias="chatChannelUrl",
        examples=["pod_20_chat"],
        description="Sendbird 채팅방 URL",
    )

    # 이미지 리스트
    images: List[PodImageDto] = Field(
        default_factory=list,
        serialization_alias="images",
        description="파티 이미지 목록",
    )

    # 개인화 필드
    is_liked: bool = Field(
        default=False, serialization_alias="isLiked", examples=[False]
    )
    my_application: Optional[SimpleApplicationDto] = Field(
        default=None,
        serialization_alias="myApplication",
        description="현재 사용자의 신청서 정보",
    )
    applications: List[SimpleApplicationDto] = Field(
        default_factory=list,
        serialization_alias="applications",
        description="파티에 들어온 신청서 목록",
    )

    # 통계 및 메타데이터 필드
    view_count: int = Field(default=0, serialization_alias="viewCount", examples=[0])
    joined_users_count: int = Field(
        default=0, serialization_alias="joinedUsersCount", examples=[0]
    )
    like_count: int = Field(default=0, serialization_alias="likeCount", examples=[0])
    joined_users: List[SimpleUserDto] = Field(
        default_factory=list,
        serialization_alias="joinedUsers",
        description="파티에 참여 중인 사용자 목록",
    )
    reviews: List["PodReviewDto"] = Field(
        default_factory=list,
        serialization_alias="reviews",
        description="파티 후기 목록",
    )
    created_at: datetime.datetime = Field(
        serialization_alias="createdAt", examples=["2025-01-01T00:00:00"]
    )
    updated_at: datetime.datetime = Field(
        serialization_alias="updatedAt", examples=["2025-01-01T00:00:00"]
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


# Forward reference 해결을 위해 PodReviewDto import 후 모델 재빌드
from app.features.pods.schemas import PodReviewDto  # noqa: E402

PodDto.model_rebuild()
