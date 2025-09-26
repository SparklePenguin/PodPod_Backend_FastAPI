# List import 제거 (Python 3.9+에서는 list 사용)
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    Request,
    Form,
    File,
    UploadFile,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.services.pod.pod_service import PodService
from app.schemas.pod import (
    PodCreateRequest,
    PodDto,
)
from app.schemas.common import (
    BaseResponse,
    PageDto,
)
from app.core.http_status import HttpStatus
from app.core.error_codes import get_error_info


router = APIRouter()


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
)
async def create_pod(
    title: str = Form(..., description="파티 제목"),
    description: Optional[str] = Form(
        ...,
        description="파티 설명",
    ),
    sub_categories: list[str] = Form(
        [],
        alias="subCategories",
        description="서브 카테고리 (예: ['EXCHANGE', 'SALE', 'GROUP_PURCHASE'] 등)",
    ),
    capacity: int = Form(..., description="최대 인원수"),
    place: str = Form(..., description="장소명"),
    address: str = Form(..., description="주소"),
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
    images: list[UploadFile] = File(..., description="파티 이미지 리스트"),
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
)
async def get_pod_detail(
    pod_id: int,
    pod_service: PodService = Depends(get_pod_service),
):
    pod = await pod_service.get_pod_detail(pod_id)
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
            "description": "파티 수정 성공 (No Content)",
        },
    },
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
            "description": "파티 삭제 성공 (No Content)",
        },
    },
)
async def delete_pod(
    pod_id: int,
    pod_service: PodService = Depends(get_pod_service),
):
    await pod_service.delete_pod(pod_id)
    return BaseResponse.ok(http_status=HttpStatus.NO_CONTENT)
