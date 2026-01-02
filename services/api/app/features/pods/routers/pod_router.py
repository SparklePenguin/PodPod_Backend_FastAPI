from typing import List

from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.service import get_pod_service, get_pod_use_case
from app.features.pods.schemas import PodDetailDto, PodForm, PodSearchRequest
from app.features.pods.services.pod_service import PodService
from app.features.pods.use_cases.pod_use_case import PodUseCase
from fastapi import APIRouter, Body, Depends, File, Query, UploadFile, status

router = APIRouter(dependencies=[])


# MARK: - 파티 생성
@router.post(
    "",
    response_model=BaseResponse[PodDetailDto],
    description="파티 생성",
)
async def create_pod(
    pod_data: PodForm = Depends(),
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


# MARK: - 인기 파티 조회
@router.get(
    "/trending",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="인기 파티 조회",
)
async def get_trending_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    pods = await pod_service.get_trending_pods(
        current_user_id, selected_artist_id, page, size
    )
    return BaseResponse.ok(data=pods)


# MARK: - 마감 직전 파티 조회
@router.get(
    "/closing-soon",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="마감 직전 파티 조회",
)
async def get_closing_soon_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    location: str | None = None,
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    pods = await pod_service.get_closing_soon_pods(
        current_user_id, selected_artist_id, location, page, size
    )
    return BaseResponse.ok(data=pods)


# MARK: - 우리 만난적 있어요 파티 조회
@router.get(
    "/history-based",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="우리 만난적 있어요 파티 조회",
)
async def get_history_based_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    pods = await pod_service.get_history_based_pods(
        current_user_id, selected_artist_id, page, size
    )
    return BaseResponse.ok(data=pods)


# MARK: - 인기 최고 카테고리 파티 조회
@router.get(
    "/popular-category",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="인기 최고 카테고리 파티 조회",
)
async def get_popular_categories_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    location: str | None = None,
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Query(1, description="사용자 ID (테스트용)"),
    pod_service: PodService = Depends(get_pod_service),
):
    pods = await pod_service.get_popular_categories_pods(
        current_user_id, selected_artist_id, location, page, size
    )
    return BaseResponse.ok(data=pods)


# MARK: - 내가 참여한 파티 목록 조회
@router.get(
    "/user/joined",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="내가 참여한 파티 목록 조회",
)
async def get_my_joined_pods(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """내가 참여한 파티 목록 조회"""
    joined_pods = await pod_service.get_user_joined_pods(current_user_id, page, size)
    return BaseResponse.ok(
        data=joined_pods,
        message_ko="내가 참여한 파티 목록을 조회했습니다.",
        message_en="Successfully retrieved my joined pods.",
    )


# MARK: - 내가 저장한 파티 목록 조회
@router.get(
    "/user/liked",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="내가 저장한 파티 목록 조회",
)
async def get_my_liked_pods(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """내가 저장한 파티 목록 조회"""
    liked_pods = await pod_service.get_user_liked_pods(current_user_id, page, size)
    return BaseResponse.ok(
        data=liked_pods,
        message_ko="내가 저장한 파티 목록을 조회했습니다.",
        message_en="Successfully retrieved my liked pods.",
    )


# MARK: - 사용자가 개설한 파티 목록 조회
@router.get(
    "/user",
    response_model=BaseResponse[PageDto[PodDetailDto]],
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
    pod_service: PodService = Depends(get_pod_service),
):
    """사용자가 개설한 파티 목록 조회"""
    target_user_id = userId if userId is not None else current_user_id
    user_pods = await pod_service.get_user_pods(target_user_id, page, size)
    return BaseResponse.ok(
        data=user_pods,
        message_ko="사용자가 개설한 파티 목록을 조회했습니다.",
        message_en="Successfully retrieved user's pods.",
    )


# MARK: - 팟 목록 조회 (검색 포함)
@router.post(
    "/search",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="팟 목록 조회",
)
async def get_pods(
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
    pod_data: PodForm = Depends(),
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
    pod_service: PodService = Depends(get_pod_service),
):
    """파티 삭제 (파티장만 가능)"""
    # 파티 조회 및 파티장 확인
    pod = await pod_service._pod_repo.get_pod_by_id(pod_id)
    if not pod:
        from app.features.pods.exceptions import PodNotFoundException
        raise PodNotFoundException(pod_id)
    
    if pod.owner_id != current_user_id:
        from app.features.pods.exceptions import NoPodAccessPermissionException
        raise NoPodAccessPermissionException(pod_id, current_user_id)
    
    await pod_service.delete_pod(pod_id)
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
    pod_service: PodService = Depends(get_pod_service),
):
    """파티 멤버 삭제 (일반 멤버만 가능, 파티장은 파티 삭제 엔드포인트 사용)"""
    # 파티 조회 및 파티장 확인
    pod = await pod_service._pod_repo.get_pod_by_id(pod_id)
    if not pod:
        from app.features.pods.exceptions import PodNotFoundException
        raise PodNotFoundException(pod_id)
    
    # user_id가 제공되면 사용, 없으면 현재 사용자 사용
    target_user_id = int(user_id) if user_id and user_id.strip() else current_user_id
    
    # 파티장인지 확인
    if pod.owner_id == target_user_id:
        from app.features.pods.exceptions import PodAccessDeniedException
        raise PodAccessDeniedException("파티장은 파티 삭제 엔드포인트를 사용해주세요.")
    
    result = await pod_service.leave_pod(pod_id, user_id, current_user_id)
    return BaseResponse.ok(
        data=result,
        message_ko="파티에서 성공적으로 나갔습니다.",
    )
