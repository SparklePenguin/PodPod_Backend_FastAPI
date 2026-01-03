"""Pod 관련 스키마들"""

from datetime import date, datetime, time
from typing import TYPE_CHECKING, List

from app.features.pods.models.pod_models import (
    PodStatus,
)
from app.features.users.schemas import UserDto
from fastapi import Form
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from app.features.pods.schemas.application_schemas import PodApplDto
    from app.features.pods.schemas.review_schemas import PodReviewDto


# - MARK: Pod DTO
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
    selected_artist_id: int | None = Field(
        default=None, alias="selectedArtistId", description="선택된 아티스트 ID"
    )
    capacity: int = Field(..., description="최대 인원수")
    place: str = Field(..., alias="meetingPlace", description="만남 장소")
    meeting_date: date = Field(..., alias="meetingDate", description="만남 날짜")
    meeting_time: time = Field(..., alias="meetingTime", description="만남 시간")
    status: PodStatus = Field(
        default=PodStatus.RECRUITING,
        description="파티 상태 (RECRUITING: 모집중, COMPLETED: 모집 완료, CLOSED: 종료, CANCELED: 취소)",
    )
    is_del: bool = Field(default=False, alias="isDel", description="삭제 여부")
    created_at: datetime = Field(..., alias="createdAt", description="생성 시간")
    updated_at: datetime = Field(..., alias="updatedAt", description="수정 시간")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Pod Detail DTO
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
    meeting_date: date = Field(..., alias="meetingDate", description="만남 날짜")
    meeting_time: time = Field(..., alias="meetingTime", description="만남 시간")
    selected_artist_id: int | None = Field(default=None, alias="selectedArtistId")
    status: PodStatus = Field(
        default=PodStatus.RECRUITING,
        description="파티 상태 (RECRUITING: 모집중, FULL: 인원 가득참, COMPLETED: 모집 완료, CLOSED: 종료)",
    )
    is_del: bool = Field(default=False, alias="isDel", description="삭제 여부")
    chat_room_id: int | None = Field(
        default=None,
        alias="chatRoomId",
        description="채팅방 ID",
    )

    # 이미지 리스트
    images: List["PodImageDto"] = Field(
        default_factory=list,
        description="파티 이미지 목록",
    )

    # 개인화 필드
    is_liked: bool = Field(default=False, alias="isLiked")
    my_application: "PodApplDto | None" = Field(
        default=None,
        alias="myApplication",
        description="현재 사용자의 신청서 정보",
    )
    applications: List["PodApplDto"] = Field(
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
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Pod Form (Form 데이터용 - FastAPI 0.95+ Form 직접 사용, 생성/수정 공통)
class PodForm(BaseModel):
    """파티 생성/수정 Form 데이터 모델 (FastAPI 0.95+ 지원)"""

    title: str | None = Form(None, description="파티 제목")
    description: str | None = Form(None, description="파티 설명")
    sub_categories: str | None = Form(
        None, alias="subCategories", description="서브 카테고리 JSON 문자열"
    )
    capacity: int | None = Form(None, description="최대 인원수")
    place: str | None = Form(None, description="장소명")
    address: str | None = Form(None, description="주소")
    sub_address: str | None = Form(None, alias="subAddress", description="상세 주소")
    x: float | None = Form(None, description="경도 (longitude)")
    y: float | None = Form(None, description="위도 (latitude)")
    meeting_date: str | None = Form(
        None,
        alias="meetingDate",
        description="만남 일시 (UTC ISO 8601, 예: 2025-11-20T12:00:00Z)",
    )
    selected_artist_id: int | None = Form(
        None, alias="selectedArtistId", description="선택된 아티스트 ID"
    )
    image_orders: str | None = Form(
        None,
        alias="imageOrders",
        description="이미지 순서 JSON 문자열 (기존: {type: 'existing', url: '...'}, 신규: {type: 'new', fileIndex: 0})",
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Pod Search Request
class PodSearchRequest(BaseModel):
    """팟 검색 요청"""

    title: str | None = Field(None, description="팟 제목")
    main_category: str | None = Field(
        None,
        alias="mainCategory",
        description="메인 카테고리 (ACCOMPANY, GOODS, TOUR, ETC)",
    )
    sub_category: str | None = Field(
        None, alias="subCategory", description="서브 카테고리"
    )
    start_date: date | None = Field(
        None, alias="startDate", description="시작 날짜"
    )
    end_date: date | None = Field(
        None, alias="endDate", description="종료 날짜"
    )
    location: List[str | None] = Field(
        None,
        description="지역 리스트 (address 또는 sub_address에 포함)",
    )
    page: int | None = Field(1, ge=1, description="페이지 번호")
    size: int | None = Field(20, alias="size", ge=1, le=100, description="페이지 크기")
    limit: int | None = Field(
        None,
        description="결과 제한 (deprecated, pageSize 사용 권장)",
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Pod Image DTO
class PodImageDto(BaseModel):
    """파티 이미지 DTO"""

    id: int = Field()
    pod_id: int = Field(alias="podId")
    image_url: str = Field(alias="imageUrl")
    thumbnail_url: str | None = Field(default=None, alias="thumbnailUrl")
    display_order: int = Field(alias="displayOrder")
    created_at: datetime | None = Field(default=None, alias="createdAt")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Pod Member DTO
class PodMemberDto(BaseModel):
    id: int = Field(description="신청서 ID")
    user: UserDto = Field()
    role: str = Field()
    message: str | None = Field(default=None, description="참여 신청 메시지")
    joined_at: datetime = Field(alias="joinedAt", description="참여 신청 시간")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: Image Order
class ImageOrderDto(BaseModel):
    """이미지 순서 정보"""

    type: str = Field(..., description="이미지 타입: 'existing' 또는 'new'")
    url: str | None = Field(None, description="기존 이미지 URL (type='existing'일 때)")
    file_index: int | None = Field(
        None,
        alias="fileIndex",
        description="새 이미지 파일 인덱스 (type='new'일 때)",
    )

    model_config = {"populate_by_name": True}
