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
from app.schemas.pod.image_order import ImageOrder
from app.schemas.common import (
    BaseResponse,
    PageDto,
)
from app.core.http_status import HttpStatus
from app.core.error_codes import get_error_info
from app.services.scheduler_service import scheduler


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
    x: Optional[float] = Form(None, alias="x", description="경도 (longitude)"),
    y: Optional[float] = Form(None, alias="y", description="위도 (latitude)"),
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
        x=x,
        y=y,
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
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
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
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
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
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
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
async def get_popular_categories_pods(
    selected_artist_id: int = Query(..., alias="selectedArtistId"),
    location: Optional[str] = None,
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
    current_user_id: int = Query(1, description="사용자 ID (테스트용)"),
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
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
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
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
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
    summary="사용자가 개설한 파티 목록 조회",
    description="특정 사용자(또는 현재 로그인한 사용자)가 개설한 파티 목록을 페이지네이션으로 조회합니다.",
    responses={
        200: {
            "description": "사용자가 개설한 파티 목록 조회 성공",
        },
    },
    tags=["pods"],
)
async def get_user_pods(
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
    userId: Optional[int] = Query(
        None,
        alias="userId",
        description="조회할 사용자 ID (없으면 현재 로그인한 사용자)",
    ),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """사용자가 개설한 파티 목록 조회"""
    try:
        # userId가 제공되지 않으면 현재 사용자 ID 사용
        target_user_id = userId if userId is not None else current_user_id

        # 먼저 해당 사용자가 존재하는지 확인
        from app.services.user_service import UserService
        from app.core.error_codes import get_error_info

        user_service = UserService(pod_service.db)
        try:
            await user_service.get_user(target_user_id)
        except Exception:
            # 사용자가 존재하지 않으면 404 오류 반환
            error_info = get_error_info("USER_NOT_FOUND")
            return BaseResponse.error(
                error_key=error_info.error_key,
                error_code=error_info.code,
                http_status=error_info.http_status,
                message_ko="사용자를 찾을 수 없습니다.",
                message_en="User not found.",
            )

        user_pods = await pod_service.get_user_pods(target_user_id, page, size)

        return BaseResponse.ok(
            data=user_pods,
            http_status=HttpStatus.OK,
            message_ko="사용자가 개설한 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved user's pods.",
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
    search_request: PodSearchRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """팟 목록을 조회합니다."""
    try:
        pod_service = PodService(db)
        result = await pod_service.search_pods(
            user_id=current_user_id,
            title=search_request.title,
            main_category=search_request.main_category,
            sub_category=search_request.sub_category,
            start_date=search_request.start_date,
            end_date=search_request.end_date,
            location=search_request.location,
            page=search_request.page or 1,
            page_size=search_request.page_size or 20,
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
    response_model=BaseResponse[PodDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PodDto],
            "description": "파티 수정 성공",
        },
    },
    summary="파티 수정",
    description="특정 파티의 정보를 수정합니다. 이미지 업로드 지원.",
    tags=["pods"],
)
async def update_pod(
    pod_id: int,
    title: Optional[str] = Form(None, alias="title", description="파티 제목"),
    description: Optional[str] = Form(
        None, alias="description", description="파티 설명"
    ),
    sub_categories: Optional[list[str]] = Form(
        None, alias="subCategories", description="서브 카테고리"
    ),
    capacity: Optional[int] = Form(None, alias="capacity", description="최대 인원수"),
    place: Optional[str] = Form(None, alias="place", description="장소명"),
    address: Optional[str] = Form(None, alias="address", description="주소"),
    sub_address: Optional[str] = Form(
        None, alias="subAddress", description="상세 주소"
    ),
    x: Optional[float] = Form(None, alias="x", description="경도 (longitude)"),
    y: Optional[float] = Form(None, alias="y", description="위도 (latitude)"),
    meeting_date: Optional[str] = Form(
        None, alias="meetingDate", description="만남 날짜 (YYYY-MM-DD)"
    ),
    meeting_time: Optional[str] = Form(
        None, alias="meetingTime", description="만남 시간 (HH:MM)"
    ),
    selected_artist_id: Optional[int] = Form(
        None, alias="selectedArtistId", description="선택된 아티스트 ID"
    ),
    image_orders: Optional[str] = Form(
        None,
        alias="imageOrders",
        description="이미지 순서 JSON 문자열 (기존: {type: 'existing', url: '...'}, 신규: {type: 'new', fileIndex: 0})",
    ),
    new_images: Optional[list[UploadFile]] = File(
        None, alias="newImages", description="새로 업로드할 이미지 파일 리스트"
    ),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """파티 정보 수정 (이미지 업로드 지원)"""
    from datetime import date, time
    import logging

    logger = logging.getLogger(__name__)

    # 모든 Form 데이터 로깅
    logger.info(f"[API] 받은 모든 Form 데이터:")
    logger.info(f"[API] - title: {title}")
    logger.info(f"[API] - description: {description}")
    logger.info(f"[API] - image_orders: '{image_orders}'")
    logger.info(f"[API] - image_orders 타입: {type(image_orders)}")
    logger.info(f"[API] - new_images 개수: {len(new_images) if new_images else 0}")

    # 업데이트할 필드들 준비
    update_fields = {}

    # 기본 정보 업데이트
    if title is not None:
        update_fields["title"] = title
    if description is not None:
        update_fields["description"] = description
    if sub_categories is not None:
        update_fields["sub_categories"] = sub_categories
    if capacity is not None:
        update_fields["capacity"] = capacity
    if place is not None:
        update_fields["place"] = place
    if address is not None:
        update_fields["address"] = address
    if sub_address is not None:
        update_fields["sub_address"] = sub_address
    if x is not None:
        update_fields["x"] = x
    if y is not None:
        update_fields["y"] = y
    if selected_artist_id is not None:
        update_fields["selected_artist_id"] = selected_artist_id

    # 날짜와 시간 파싱
    if meeting_date is not None:
        update_fields["meeting_date"] = date.fromisoformat(meeting_date)
    if meeting_time is not None:
        update_fields["meeting_time"] = time.fromisoformat(meeting_time)

    # 파티 업데이트 실행 (이미지 포함)
    updated_pod = await pod_service.update_pod_with_images(
        pod_id=pod_id,
        current_user_id=current_user_id,
        update_fields=update_fields,
        image_orders=image_orders,
        new_images=new_images,
    )

    if updated_pod is None:
        error_info = get_error_info("POD_UPDATE_FAILED")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=HttpStatus.BAD_REQUEST,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )

    return BaseResponse.ok(data=updated_pod)


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


# - MARK: 파티 상태 업데이트 (JSON 요청 본문 방식 - 더 RESTful)
@router.patch(
    "/{pod_id}/status",
    response_model=BaseResponse[PodDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PodDto],
            "description": "파티 상태 업데이트 성공",
        },
        HttpStatus.NOT_FOUND: {
            "model": BaseResponse[None],
            "description": "파티를 찾을 수 없음",
        },
        HttpStatus.FORBIDDEN: {
            "model": BaseResponse[None],
            "description": "권한 없음 (파티장이 아님)",
        },
        HttpStatus.BAD_REQUEST: {
            "model": BaseResponse[None],
            "description": "잘못된 요청 데이터",
        },
    },
    summary="파티 상태 업데이트",
    description="파티장이 파티의 상태를 변경합니다. (RECRUITING, COMPLETED, CLOSED 등)",
    tags=["pods"],
)
async def update_pod_status(
    pod_id: int,
    request: dict = Body(
        ..., description="상태 업데이트 요청", example={"status": "COMPLETED"}
    ),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """파티 상태 업데이트 (JSON 요청 본문 방식)"""
    from app.models.pod.pod_status import PodStatus

    # 요청 데이터 검증
    if "status" not in request:
        return BaseResponse.error(
            error_key="MISSING_STATUS",
            error_code=4000,
            http_status=HttpStatus.BAD_REQUEST,
            message_ko="status 필드가 필요합니다.",
            message_en="status field is required",
        )

    status_value = request["status"]

    # 상태 값 검증
    try:
        pod_status = PodStatus(status_value.upper())
    except ValueError:
        return BaseResponse.error(
            error_key="INVALID_STATUS",
            error_code=4000,
            http_status=HttpStatus.BAD_REQUEST,
            message_ko=f"잘못된 상태 값입니다. 가능한 값: {', '.join([s.value for s in PodStatus])}",
            message_en=f"Invalid status value. Available values: {', '.join([s.value for s in PodStatus])}",
        )

    success = await pod_service.update_pod_status_by_owner(
        pod_id, pod_status, current_user_id
    )
    if success:
        # 업데이트된 파티 정보 반환
        updated_pod = await pod_service.get_pod_detail(pod_id, current_user_id)
        return BaseResponse.ok(
            data=updated_pod,
            message_ko=f"파티 상태가 {pod_status.value}로 성공적으로 변경되었습니다.",
        )
    else:
        return BaseResponse.error(
            error_key="POD_UPDATE_FAILED",
            error_code=5000,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko="파티 상태 업데이트에 실패했습니다.",
            message_en="Failed to update pod status",
        )


# - MARK: 파티 멤버 삭제 (토큰 기반)
@router.delete(
    "/{pod_id}/member",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "파티 멤버 삭제 성공",
        },
        HttpStatus.NOT_FOUND: {
            "model": BaseResponse[None],
            "description": "파티를 찾을 수 없음",
        },
        HttpStatus.FORBIDDEN: {
            "model": BaseResponse[None],
            "description": "권한 없음 (파티 멤버가 아님)",
        },
    },
    summary="파티 멤버 삭제",
    description="사용자 ID가 제공되면 해당 사용자를, 없으면 현재 사용자를 파티 멤버에서 삭제합니다. 파티장이 삭제되면 모든 멤버가 강제 퇴장되고 파티가 종료됩니다.",
    tags=["pods"],
)
async def delete_pod_member(
    pod_id: int,
    user_id: Optional[str] = Query(
        default=None,
        description="삭제할 사용자 ID (없으면 현재 사용자)",
        alias="userId",
    ),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    """파티 멤버 삭제 (사용자 ID 선택적)"""
    # user_id가 제공되면 사용, 없으면 토큰에서 추출한 사용자 ID 사용
    if user_id is not None and user_id.strip() != "":
        try:
            target_user_id = int(user_id)
        except ValueError:
            # 잘못된 정수 형식인 경우 현재 사용자 사용
            target_user_id = current_user_id
    else:
        target_user_id = current_user_id

    result = await pod_service.leave_pod(pod_id, target_user_id)

    if result["is_owner"]:
        message = f"파티장이 나가서 파티가 종료되었습니다. {result['members_removed']}명의 멤버가 함께 나갔습니다."
    else:
        message = "파티에서 성공적으로 나갔습니다."

    return BaseResponse.ok(
        data=result,
        message_ko=message,
    )


@router.post(
    "/test-scheduler",
    summary="스케줄러 테스트",
    description="파티 시작 임박 알림 스케줄러를 수동으로 실행합니다.",
    tags=["pods"],
)
async def test_scheduler(
    db: AsyncSession = Depends(get_db),
):
    """스케줄러 테스트"""
    try:
        await scheduler._send_start_soon_reminders(db)
        return BaseResponse.ok(data=None, message_ko="스케줄러 테스트 완료")
    except Exception as e:
        return BaseResponse.ok(
            data={"error": str(e)}, message_ko=f"스케줄러 테스트 실패: {e}"
        )


@router.get(
    "/debug-pods",
    summary="파티 디버그",
    description="모든 파티 정보를 조회합니다.",
    tags=["pods"],
)
async def debug_pods(
    db: AsyncSession = Depends(get_db),
):
    """파티 디버그"""
    from sqlalchemy import select
    from app.models.pod.pod import Pod

    try:
        query = select(Pod).order_by(Pod.id.desc()).limit(10)
        result = await db.execute(query)
        pods = result.scalars().all()

        pod_data = []
        for pod in pods:
            pod_data.append(
                {
                    "id": pod.id,
                    "title": pod.title,
                    "meeting_date": str(pod.meeting_date),
                    "meeting_time": str(pod.meeting_time),
                    "status": pod.status,
                    "created_at": str(pod.created_at),
                }
            )

        return BaseResponse.ok(data=pod_data, message_ko="파티 디버그 완료")
    except Exception as e:
        return BaseResponse.ok(
            data={"error": str(e)}, message_ko=f"파티 디버그 실패: {e}"
        )


@router.patch(
    "/88/fix-date",
    summary="파티 88번 날짜 수정",
    description="파티 88번의 날짜를 오늘로 수정합니다.",
    tags=["pods"],
)
async def fix_pod88_date(
    db: AsyncSession = Depends(get_db),
):
    """파티 88번 날짜 수정"""
    from sqlalchemy import select, update
    from app.models.pod.pod import Pod
    from datetime import date

    try:
        # 파티 88번 조회
        query = select(Pod).where(Pod.id == 88)
        result = await db.execute(query)
        pod = result.scalar_one_or_none()

        if not pod:
            return BaseResponse.ok(
                data=None, message_ko="파티 88번을 찾을 수 없습니다."
            )

        # 날짜를 오늘로 수정
        update_query = update(Pod).where(Pod.id == 88).values(meeting_date=date.today())
        await db.execute(update_query)
        await db.commit()

        return BaseResponse.ok(
            data=None, message_ko="파티 88번 날짜가 오늘로 수정되었습니다."
        )
    except Exception as e:
        return BaseResponse.ok(
            data={"error": str(e)}, message_ko=f"파티 88번 날짜 수정 실패: {e}"
        )


@router.post(
    "/test-review-notification",
    summary="리뷰 알림 테스트",
    description="리뷰 유도 알림을 수동으로 전송합니다.",
    tags=["pods"],
)
async def test_review_notification(
    db: AsyncSession = Depends(get_db),
):
    """리뷰 알림 테스트"""
    try:
        await scheduler._send_day_reminders(db)
        return BaseResponse.ok(data=None, message_ko="리뷰 알림 테스트 완료")
    except Exception as e:
        return BaseResponse.ok(
            data={"error": str(e)}, message_ko=f"리뷰 알림 테스트 실패: {e}"
        )


@router.post(
    "/cleanup-null-notifications",
    summary="null 알림 정리",
    description="relatedId가 null인 알림들을 삭제합니다.",
    tags=["pods"],
)
async def cleanup_null_notifications(
    db: AsyncSession = Depends(get_db),
):
    """null 알림 정리"""
    from sqlalchemy import delete
    from app.models.notification import Notification

    try:
        # relatedId가 null인 알림들 삭제
        delete_query = delete(Notification).where(Notification.related_id.is_(None))
        result = await db.execute(delete_query)
        await db.commit()

        deleted_count = result.rowcount
        return BaseResponse.ok(
            data={"deleted_count": deleted_count},
            message_ko=f"{deleted_count}개의 null 알림이 삭제되었습니다.",
        )
    except Exception as e:
        return BaseResponse.ok(
            data={"error": str(e)}, message_ko=f"null 알림 정리 실패: {e}"
        )


@router.get(
    "/debug-notifications",
    summary="알림 디버그",
    description="POD_START_SOON 알림들을 조회합니다.",
    tags=["pods"],
)
async def debug_notifications(
    db: AsyncSession = Depends(get_db),
):
    """알림 디버그"""
    from sqlalchemy import select
    from app.models.notification import Notification

    try:
        query = (
            select(Notification)
            .where(Notification.notification_value == "POD_START_SOON")
            .order_by(Notification.created_at.desc())
            .limit(10)
        )

        result = await db.execute(query)
        notifications = result.scalars().all()

        notification_data = []
        for notification in notifications:
            notification_data.append(
                {
                    "id": notification.id,
                    "user_id": notification.user_id,
                    "related_pod_id": notification.related_pod_id,
                    "related_id": notification.related_id,
                    "notification_value": notification.notification_value,
                    "created_at": str(notification.created_at),
                    "title": notification.title,
                    "body": notification.body,
                }
            )

        return BaseResponse.ok(data=notification_data, message_ko="알림 디버그 완료")
    except Exception as e:
        return BaseResponse.ok(
            data={"error": str(e)}, message_ko=f"알림 디버그 실패: {e}"
        )
