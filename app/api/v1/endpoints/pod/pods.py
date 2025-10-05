from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    Request,
    Form,
    File,
    UploadFile,
    Query,
    Body,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.services.pod.pod_service import PodService
from app.schemas.pod import (
    PodCreateRequest,
    PodDto,
)
from app.schemas.pod.pod_dto import PodSearchRequest
from app.schemas.common import (
    BaseResponse,
    PageDto,
)
from app.core.http_status import HttpStatus
from app.core.error_codes import get_error_info


router = APIRouter(dependencies=[])


def get_pod_service(
    db: AsyncSession = Depends(get_db),
) -> PodService:
    return PodService(db)


# - MARK: 파티 생성
@router.post(
    "",
    response_model=BaseResponse[PodDto],
    responses={
        HttpStatus.CREATED: {
            "model": BaseResponse[PodDto],
            "description": "파티 생성 성공",
        },
    },
    summary="파티 생성",
    description="새로운 파티를 생성합니다.",
    tags=["pods"],
)
async def create_pod(
    title: str = Form(..., alias="title", description="파티 제목"),
    description: Optional[str] = Form(
        ...,
        alias="description",
        description="파티 설명",
    ),
    sub_categories: list[str] = Form(
        [],
        alias="subCategories",
        description="서브 카테고리 (예: ['EXCHANGE', 'SALE', 'GROUP_PURCHASE'] 등)",
    ),
    capacity: int = Form(..., alias="capacity", description="최대 인원수"),
    place: str = Form(..., alias="place", description="장소명"),
    address: str = Form(..., alias="address", description="주소"),
    sub_address: Optional[str] = Form(
        None, alias="subAddress", description="상세 주소"
    ),
    meeting_date: str = Form(
        ...,
        alias="meetingDate",
        description="만남 날짜 (YYYY-MM-DD)",
    ),
    meeting_time: str = Form(
        ...,
        alias="meetingTime",
        description="만남 시간 (HH:MM)",
    ),
    selected_artist_id: int = Form(
        ...,
        alias="selectedArtistId",
        description="선택된 아티스트 ID",
    ),
    images: list[UploadFile] = File(
        ..., alias="images", description="파티 이미지 리스트"
    ),
    user_id: int = Depends(get_current_user_id),
    service: PodService = Depends(get_pod_service),
):
    # sub_categories는 이미 리스트이므로 그대로 사용
    sub_category_list = sub_categories

    # 날짜와 시간 파싱
    from datetime import date, time

    parsed_meeting_date = date.fromisoformat(meeting_date)
    parsed_meeting_time = time.fromisoformat(meeting_time)

    # PodCreateRequest 객체 생성
    req = PodCreateRequest(
        title=title,
        description=description,
        sub_categories=sub_category_list,
        capacity=capacity,
        place=place,
        address=address,
        sub_address=sub_address,
        meetingDate=parsed_meeting_date,
        meetingTime=parsed_meeting_time,
        selected_artist_id=selected_artist_id,
    )

    pod = await service.create_pod(
        owner_id=user_id,
        req=req,
        images=images,
    )
    if pod is None:
        error_info = get_error_info("POD_CREATION_FAILED")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=HttpStatus.BAD_REQUEST,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )
    return BaseResponse.ok(
        data=pod,
        http_status=HttpStatus.CREATED,
    )


# - MARK: 인기 파티 조회
@router.get(
    "/trending",
    response_model=BaseResponse[PageDto[PodDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[PodDto]],
            "description": "인기 파티 조회 성공",
        },
    },
    summary="요즘 인기 있는 파티 조회",
    description="현재 선택된 아티스트 기준으로 마감되지 않은 인기 파티를 조회합니다.",
)
async def get_trending_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    page: int = 1,
    size: int = 20,
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """
    요즘 인기 있는 파티 조회

    조건:
    - 현재 선택된 아티스트 기준
    - 마감되지 않은 파티

    정렬 우선순위:
    1. 최근 7일 이내 가장 많이 지원한 팟 (지원자가 동일 덕메 성향 우선)
    2. 최근 7일 이내 조회한 팟 (조회자가 동일 덕메 성향 우선)

    페이지네이션:
    - page: 페이지 번호 (기본값: 1)
    - size: 페이지 크기 (기본값: 20)
    """
    pods = await pod_service.get_trending_pods(
        current_user_id, selected_artist_id, page, size
    )
    return BaseResponse.ok(data=pods)


# - MARK: 마감 직전 파티 조회
@router.get(
    "/closing-soon",
    response_model=BaseResponse[PageDto[PodDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[PodDto]],
            "description": "마감 직전 파티 조회 성공",
        },
    },
    summary="마감 직전 파티 조회",
    description="현재 선택된 아티스트 기준으로 마감되지 않은 마감 직전 파티를 조회합니다.",
)
async def get_closing_soon_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    location: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """
    마감 직전 파티 조회

    조건:
    - 현재 선택된 아티스트 기준
    - 마감되지 않은 파티
    - 에디터가 설정한 지역 (선택사항)

    정렬 우선순위:
    1. 신청 마감 시간이 24시간 이내인 모임 우선

    페이지네이션:
    - page: 페이지 번호 (기본값: 1)
    - size: 페이지 크기 (기본값: 20)
    """
    pods = await pod_service.get_closing_soon_pods(
        current_user_id, selected_artist_id, location, page, size
    )
    return BaseResponse.ok(data=pods)


# - MARK: 우리 만난적 있어요 파티 조회
@router.get(
    "/history-based",
    response_model=BaseResponse[PageDto[PodDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[PodDto]],
            "description": "우리 만난적 있어요 파티 조회 성공",
        },
    },
    summary="우리 만난적 있어요 파티 조회",
    description="이전 매칭 사용자와 유사한 모임을 기반으로 파티를 추천합니다.",
)
async def get_history_based_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    page: int = 1,
    size: int = 20,
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """
    우리 만난적 있어요 파티 조회

    조건:
    - 현재 선택된 아티스트 기준
    - 마감되지 않은 파티

    정렬 우선순위:
    1. 참여한 팟(평점 4점 이상, 90일 이내)의 개설자가 개설한 팟
       - 가장 최근에 참여한 5개의 팟의 카테고리와 동일한 카테고리 우선
       - 가장 최근에 참여한 5개의 팟의 동일한 지역의 모임 우선
    2. 유저가 개설한 팟에 참여한 유저(90일 이내)가 개설한 모임
       - 가장 최근에 참여한 5개의 팟의 카테고리와 동일한 카테고리 우선
       - 가장 최근에 참여한 5개의 팟의 동일한 지역의 모임 우선

    페이지네이션:
    - page: 페이지 번호 (기본값: 1)
    - size: 페이지 크기 (기본값: 20)
    """
    pods = await pod_service.get_history_based_pods(
        current_user_id, selected_artist_id, page, size
    )
    return BaseResponse.ok(data=pods)


# - MARK: 인기 최고 카테고리 파티 조회
@router.get(
    "/popular-category",
    response_model=BaseResponse[PageDto[PodDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[PodDto]],
            "description": "인기 최고 카테고리 파티 조회 성공",
        },
    },
    summary="인기 최고 카테고리 파티 조회",
    description="최근 일주일 기준 인기 카테고리 기반으로 파티를 추천합니다.",
)
async def get_popular_category_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    location: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """
    인기 최고 카테고리 파티 조회

    조건:
    - 현재 선택된 아티스트 기준
    - 마감되지 않은 파티
    - 최근 일주일 기준 가장 많이 개설된 카테고리 && 최근 일주일 기준 가장 조회가 많은 카테고리

    정렬 우선순위:
    1. 에디터가 설정한 지역의 모임 우선 (선택사항)
    2. 조회수 높은 순

    페이지네이션:
    - page: 페이지 번호 (기본값: 1)
    - size: 페이지 크기 (기본값: 20)
    """
    pods = await pod_service.get_popular_categories_pods(
        current_user_id, selected_artist_id, location, page, size
    )
    return BaseResponse.ok(data=pods)


# - MARK: 파티 상세 조회
@router.get(
    "/{pod_id}",
    response_model=BaseResponse[PodDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PodDto],
            "description": "파티 상세 조회 성공",
        },
    },
    summary="파티 상세 조회",
    description="특정 파티의 상세 정보를 조회합니다. 토큰이 있으면 사용자의 신청서 정보도 포함됩니다.",
    tags=["pods"],
)
async def get_pod_detail(
    pod_id: int,
    pod_service: PodService = Depends(get_pod_service),
    user_id: Optional[int] = Depends(get_current_user_id),
):
    pod = await pod_service.get_pod_detail(pod_id, user_id)
    if pod is None:
        error_info = get_error_info("POD_NOT_FOUND")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=HttpStatus.NOT_FOUND,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )

    return BaseResponse.ok(data=pod)


# - MARK: 파티 수정
@router.put(
    "/{pod_id}",
    response_model=BaseResponse[None],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[None],
            "description": "파티 수정 성공",
        },
    },
    summary="파티 수정",
    description="특정 파티의 정보를 수정합니다.",
    tags=["pods"],
)
async def update_pod(
    pod_id: int,
    pod_service: PodService = Depends(get_pod_service),
):
    await pod_service.update_pod(pod_id)
    return BaseResponse.ok()


# - MARK: 파티 삭제
@router.delete(
    "/{pod_id}",
    status_code=HttpStatus.NO_CONTENT,
    responses={
        HttpStatus.NO_CONTENT: {
            "description": "파티 삭제 성공",
        },
    },
    summary="파티 삭제",
    description="특정 파티를 삭제합니다.",
    tags=["pods"],
)
async def delete_pod(
    pod_id: int,
    pod_service: PodService = Depends(get_pod_service),
):
    await pod_service.delete_pod(pod_id)
    return BaseResponse.ok(http_status=HttpStatus.NO_CONTENT)


@router.get(
    "/user/{user_id}",
    response_model=BaseResponse[PageDto[PodDto]],
    summary="특정 유저가 개설한 파티 목록 조회",
    description="특정 유저가 개설한 파티 목록을 페이지네이션으로 조회합니다.",
    responses={
        200: {
            "description": "특정 유저의 파티 목록 조회 성공",
        },
    },
    tags=["pods"],
)
async def get_user_pods(
    user_id: int,
    page: int = Query(1, ge=1, alias="page", description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, alias="size", description="페이지 크기"),
    pod_service: PodService = Depends(get_pod_service),
):
    """특정 유저가 개설한 파티 목록 조회"""
    try:
        user_pods = await pod_service.get_user_pods(user_id, page, size)

        return BaseResponse.ok(
            data=user_pods,
            http_status=HttpStatus.OK,
            message_ko="유저의 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved user's pods.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )


@router.get(
    "/user/joined",
    response_model=BaseResponse[PageDto[PodDto]],
    summary="내가 참여한 파티 목록 조회",
    description="현재 로그인한 사용자가 참여한 파티 목록을 페이지네이션으로 조회합니다.",
    responses={
        200: {
            "description": "내가 참여한 파티 목록 조회 성공",
        },
    },
    tags=["pods"],
)
async def get_my_joined_pods(
    page: int = Query(1, ge=1, alias="page", description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, alias="size", description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """내가 참여한 파티 목록 조회"""
    try:
        joined_pods = await pod_service.get_user_joined_pods(
            current_user_id, page, size
        )

        return BaseResponse.ok(
            data=joined_pods,
            http_status=HttpStatus.OK,
            message_ko="내가 참여한 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved my joined pods.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )


@router.get(
    "/user/liked",
    response_model=BaseResponse[PageDto[PodDto]],
    summary="내가 저장한 파티 목록 조회",
    description="현재 로그인한 사용자가 좋아요한 파티 목록을 페이지네이션으로 조회합니다.",
    responses={
        200: {
            "description": "내가 저장한 파티 목록 조회 성공",
        },
    },
    tags=["pods"],
)
async def get_my_liked_pods(
    page: int = Query(1, ge=1, alias="page", description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, alias="size", description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """내가 저장한 파티 목록 조회"""
    try:
        liked_pods = await pod_service.get_user_liked_pods(current_user_id, page, size)

        return BaseResponse.ok(
            data=liked_pods,
            http_status=HttpStatus.OK,
            message_ko="내가 저장한 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved my liked pods.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )


@router.get(
    "/user",
    response_model=BaseResponse[PageDto[PodDto]],
    summary="내가 개설한 파티 목록 조회",
    description="현재 로그인한 사용자가 개설한 파티 목록을 페이지네이션으로 조회합니다.",
    responses={
        200: {
            "description": "내가 개설한 파티 목록 조회 성공",
        },
    },
    tags=["pods"],
)
async def get_my_pods(
    page: int = Query(1, ge=1, alias="page", description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, alias="size", description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """내가 개설한 파티 목록 조회"""
    try:
        user_pods = await pod_service.get_user_pods(current_user_id, page, size)

        return BaseResponse.ok(
            data=user_pods,
            http_status=HttpStatus.OK,
            message_ko="내가 개설한 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved my pods.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="유저의 파티 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving user's pods.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


# - MARK: 팟 목록 조회 (검색 포함)
@router.post(
    "/search",
    response_model=BaseResponse[PageDto[PodDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[PodDto]],
            "description": "팟 목록 조회 성공",
        },
    },
    summary="팟 목록 조회",
    description="팟 목록을 조회합니다. 검색 조건을 body로 제공하면 필터링된 결과를 반환합니다.",
    tags=["pods"],
)
async def get_pods(
    search_request: PodSearchRequest = Body(default_factory=PodSearchRequest),
    _: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """팟 목록을 조회합니다."""
    try:
        pod_service = PodService(db)
        result = await pod_service.search_pods(
            title=search_request.title,
            sub_category=search_request.sub_category,
            start_date=search_request.start_date,
            end_date=search_request.end_date,
            location=search_request.location,
            page=search_request.page,
            page_size=search_request.page_size,
        )

        return BaseResponse.ok(result, message_ko="팟 목록 조회 성공", http_status=200)

    except ValueError as e:
        error_info = get_error_info("INVALID_REQUEST")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="잘못된 날짜 형식입니다.",
            message_en="Invalid date format.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=str(e),
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="팟 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving pods.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=str(e),
        )
