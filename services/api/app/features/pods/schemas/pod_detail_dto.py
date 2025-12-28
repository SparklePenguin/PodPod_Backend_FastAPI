import datetime
import json

# 순환 import 방지를 위한 TYPE_CHECKING
from typing import TYPE_CHECKING, Any, List

from app.features.pods.models.pod.pod_enums import (
    AccompanySubCategory,
    EtcSubCategory,
    GoodsSubCategory,
    TourSubCategory,
)
from app.features.pods.models.pod.pod_status import PodStatus
from app.features.pods.schemas.pod_appl_dto import PodApplDto
from app.features.pods.schemas.pod_image_dto import PodImageDto
from app.features.users.schemas import UserDto
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from app.features.pods.schemas import PodReviewDto


class PodDetailDto(BaseModel):
    id: int = Field()
    owner_id: int = Field(alias="ownerId")
    title: str = Field()
    description: str = Field()
    image_url: str | None = Field(default=None, alias="imageUrl")
    thumbnail_url: str | None = Field(default=None, alias="thumbnailUrl")
    sub_categories: List[str] = Field(alias="subCategories")
    capacity: int = Field()
    place: str = Field(alias="meetingPlace")
    address: str = Field()
    sub_address: str | None = Field(default=None, alias="subAddress")
    x: float | None = Field(default=None, description="경도 (longitude)")
    y: float | None = Field(default=None, description="위도 (latitude)")
    meeting_date: int | None = Field(
        alias="meetingDate",
        description="만남 날짜/시간 (timestamp in milliseconds)",
    )
    selected_artist_id: int | None = Field(default=None, alias="selectedArtistId")
    status: PodStatus = Field(
        default=PodStatus.RECRUITING,
        description="파티 상태 (RECRUITING: 모집중, FULL: 인원 가득참, COMPLETED: 모집 완료, CLOSED: 종료)",
    )
    chat_channel_url: str | None = Field(
        default=None,
        alias="chatChannelUrl",
        description="Sendbird 채팅방 URL",
    )

    # 이미지 리스트
    images: List[PodImageDto] = Field(
        default_factory=list,
        description="파티 이미지 목록",
    )

    # 개인화 필드
    is_liked: bool = Field(default=False, alias="isLiked")
    my_application: PodApplDto | None = Field(
        default=None,
        alias="myApplication",
        description="현재 사용자의 신청서 정보",
    )
    applications: List[PodApplDto] = Field(
        default_factory=list,
        description="파티에 들어온 신청서 목록",
    )

    # 통계 및 메타데이터 필드
    view_count: int = Field(default=0, alias="viewCount")
    joined_users_count: int = Field(default=0, alias="joinedUsersCount")
    like_count: int = Field(default=0, alias="likeCount")
    joined_users: List[UserDto] = Field(
        default_factory=list,
        alias="joinedUsers",
        description="파티에 참여 중인 사용자 목록",
    )
    reviews: List["PodReviewDto"] = Field(
        default_factory=list,
        description="파티 후기 목록",
    )
    created_at: datetime.datetime = Field(alias="createdAt")
    updated_at: datetime.datetime = Field(alias="updatedAt")

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
from app.features.pods.schemas.pod_review_dto import PodReviewDto  # noqa: E402

PodDetailDto.model_rebuild()
