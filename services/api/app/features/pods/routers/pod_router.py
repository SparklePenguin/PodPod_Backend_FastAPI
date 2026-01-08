from typing import List

from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.pod_form import get_pod_form, get_pod_form_for_update
from app.deps.providers import get_pod_service, get_pod_use_case
from app.features.pods.schemas import PodDetailDto, PodDto, PodForm, PodSearchRequest
from app.features.pods.services.pod_service import PodService
from app.features.pods.use_cases.pod_use_case import PodUseCase
from fastapi import APIRouter, Body, Depends, File, Query, UploadFile, status

router = APIRouter(prefix="/pods", tags=["pods"])


# MARK: - 파티 생성
@router.post(
    "",
    response_model=BaseResponse[PodDetailDto],
    description="파티 생성",
)
async def create_pod(
    pod_data: PodForm = Depends(get_pod_form),
    images: List[UploadFile] = File(..., description="파티 이미지 리스트"),
    user_id: int = Depends(get_current_user_id),
    service: PodService = Depends(get_pod_service),
):
    """파티 생성"""
    pod = await service.create_pod_from_form(
        owner_id=user_id,
        pod_form=pod_data,
        images=images,
    )
    return BaseResponse.ok(data=pod, http_status=status.HTTP_201_CREATED)


# MARK: - 파티 타입 목록 조회
@router.get(
    "/types",
    response_model=BaseResponse[dict],
    description="파티 목록 조회 가능한 타입 목록",
)
async def get_pod_types():
    """사용 가능한 파티 타입 목록 조회"""
    types = {
        "types": [
            {
                "value": "trending",
                "label_ko": "인기 파티",
                "label_en": "Trending Pods",
                "description_ko": "인기 파티 목록",
                "description_en": "List of trending pods",
            },
            {
                "value": "closing-soon",
                "label_ko": "마감 직전 파티",
                "label_en": "Closing Soon Pods",
                "description_ko": "마감 직전 파티 목록",
                "description_en": "List of pods closing soon",
            },
            {
                "value": "history-based",
                "label_ko": "우리 만난적 있어요",
                "label_en": "History Based Pods",
                "description_ko": "우리 만난적 있어요 파티 목록",
                "description_en": "List of history-based pods",
            },
            {
                "value": "popular-category",
                "label_ko": "인기 카테고리",
                "label_en": "Popular Category Pods",
                "description_ko": "인기 카테고리 파티 목록",
                "description_en": "List of popular category pods",
            },
            {
                "value": "joined",
                "label_ko": "참여한 파티",
                "label_en": "Joined Pods",
                "description_ko": "내가 참여한 파티 목록",
                "description_en": "List of pods I joined",
            },
            {
                "value": "liked",
                "label_ko": "저장한 파티",
                "label_en": "Liked Pods",
                "description_ko": "내가 저장한 파티 목록",
                "description_en": "List of pods I liked",
            },
            {
                "value": "owned",
                "label_ko": "개설한 파티",
                "label_en": "Owned Pods",
                "description_ko": "내가 개설한 파티 목록",
                "description_en": "List of pods I created",
            },
            {
                "value": "following",
                "label_ko": "팔로우한 사용자들의 파티",
                "label_en": "Following Users' Pods",
                "description_ko": "팔로우하는 사용자들이 만든 파티 목록",
                "description_en": "List of pods created by users I follow",
            },
        ]
    }
    return BaseResponse.ok(
        data=types,
        message_ko="파티 타입 목록을 조회했습니다.",
        message_en="Successfully retrieved pod types.",
    )


# MARK: - 파티 목록 조회 (통합)
@router.get(
    "",
    response_model=BaseResponse[PageDto[PodDto]],
    description="파티 목록 조회 (type: trending, closing-soon, history-based, popular-category, joined, liked, owned, following)",
)
async def get_pods_by_type(
    type: str = Query(
        ...,
        description="파티 타입: trending(인기), closing-soon(마감직전), history-based(우리만난적있어요), popular-category(인기카테고리), joined(참여한), liked(저장한), owned(개설한), following(팔로우한 사용자들의 파티)",
        regex="^(trending|closing-soon|history-based|popular-category|joined|liked|owned|following)$",
    ),
    selected_artist_id: int | None = Query(
        None,
        alias="selectedArtistId",
        description="선택된 아티스트 ID (trending, closing-soon, history-based, popular-category 타입에 필요)",
    ),
    location: str | None = Query(
        None,
        description="지역 필터 (closing-soon, popular-category 타입에 선택사항)",
    ),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    pod_use_case: PodUseCase = Depends(get_pod_use_case),
):
    """파티 목록 조회"""
    pods, message_ko, message_en = await pod_use_case.get_pods_by_type(
        user_id=current_user_id,
        pod_type=type,
        selected_artist_id=selected_artist_id,
        location=location,
        page=page,
        size=size,
    )
    return BaseResponse.ok(data=pods, message_ko=message_ko, message_en=message_en)


# MARK: - 사용자가 개설한 파티 목록 조회 (다른 사용자 조회용)
@router.get(
    "/user",
    response_model=BaseResponse[PageDto[PodDto]],
    description="사용자가 개설한 파티 목록 조회",
)
async def get_user_pods(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    userId: int | None = Query(
        None,
        alias="userId",
        description="조회할 사용자 ID (없으면 현재 로그인한 사용자)",
    ),
    current_user_id: int = Depends(get_current_user_id),
    pod_use_case: PodUseCase = Depends(get_pod_use_case),
):
    """사용자가 개설한 파티 목록 조회"""
    target_user_id = userId if userId is not None else current_user_id
    user_pods = await pod_use_case.get_user_pods(target_user_id, page, size)
    return BaseResponse.ok(
        data=user_pods,
        message_ko="사용자가 개설한 파티 목록을 조회했습니다.",
        message_en="Successfully retrieved user's pods.",
    )


# MARK: - 팟 목록 조회 (검색 포함)
@router.post(
    "/search",
    response_model=BaseResponse[PageDto[PodDto]],
    description="팟 목록 조회",
)
async def search_pods(
    search_request: PodSearchRequest,
    current_user_id: int = Depends(get_current_user_id),
    pod_use_case: PodUseCase = Depends(get_pod_use_case),
):
    """팟 목록을 조회합니다."""
    result = await pod_use_case.search_pods(
        user_id=current_user_id,
        search_request=search_request,
    )
    return BaseResponse.ok(data=result, message_ko="팟 목록 조회 성공")


# - MARK: 파티 상세 조회
@router.get(
    "/{pod_id}",
    response_model=BaseResponse[PodDetailDto],
    description="파티 상세 조회",
)
async def get_pod_detail(
    pod_id: int,
    pod_service: PodService = Depends(get_pod_service),
    user_id: int | None = Depends(get_current_user_id),
):
    pod = await pod_service.get_pod_detail(pod_id, user_id)
    return BaseResponse.ok(data=pod)


# - MARK: 파티 수정
@router.put(
    "/{pod_id}",
    response_model=BaseResponse[PodDetailDto],
    description="파티 수정",
)
async def update_pod(
    pod_id: int,
    pod_data: PodForm = Depends(get_pod_form_for_update),
    new_images: list[UploadFile | None] = File(
        None,
        alias="newImages",
        description="새로 업로드할 이미지 파일 리스트",
    ),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """파티 수정"""
    updated_pod = await pod_service.update_pod_from_form(
        pod_id=pod_id,
        current_user_id=current_user_id,
        pod_form=pod_data,
        new_images=new_images,
    )
    return BaseResponse.ok(data=updated_pod)


# MARK: - 파티 삭제
@router.delete(
    "/{pod_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="파티 삭제 (파티장만 가능)",
)
async def delete_pod(
    pod_id: int,
    current_user_id: int = Depends(get_current_user_id),
    pod_use_case: PodUseCase = Depends(get_pod_use_case),
):
    """파티 삭제 (파티장만 가능)"""
    await pod_use_case.delete_pod(pod_id, current_user_id)
    return BaseResponse.ok(http_status=status.HTTP_204_NO_CONTENT)


# MARK: - 파티 상태 업데이트
@router.patch(
    "/{pod_id}/status",
    response_model=BaseResponse[PodDetailDto],
    description="파티 상태 업데이트",
)
async def update_pod_status(
    pod_id: int,
    request: dict = Body(..., description="상태 업데이트 요청"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """파티 상태 업데이트"""
    status_value = request.get("status")
    updated_pod = await pod_service.update_pod_status_by_owner(
        pod_id, status_value, current_user_id
    )
    return BaseResponse.ok(
        data=updated_pod,
        message_ko=f"파티 상태가 {status_value}로 성공적으로 변경되었습니다.",
    )


# MARK: - 파티 멤버 삭제
@router.delete(
    "/{pod_id}/member",
    response_model=BaseResponse[dict],
    description="파티 멤버 삭제",
)
async def delete_pod_member(
    pod_id: int,
    user_id: str | None = Query(
        default=None,
        description="삭제할 사용자 ID (없으면 현재 사용자)",
        alias="userId",
    ),
    current_user_id: int = Depends(get_current_user_id),
    pod_use_case: PodUseCase = Depends(get_pod_use_case),
):
    """파티 멤버 삭제 (일반 멤버만 가능, 파티장은 파티 삭제 엔드포인트 사용)"""
    result = await pod_use_case.leave_pod(pod_id, user_id, current_user_id)
    return BaseResponse.ok(
        data=result,
        message_ko="파티에서 성공적으로 나갔습니다.",
    )
