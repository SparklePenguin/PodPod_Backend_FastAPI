from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.services.pod.pod_service import PodService
from app.schemas.pod import (
    PodCreateRequest,
    PodDto,
)
from app.schemas.pod.pod_openapi_schemas import POD_CREATE_REQUEST_SCHEMA
from app.schemas.common import (
    BaseResponse,
    PageDto,
)
from app.core.http_status import HttpStatus
from app.utils.form_parser import parse_form_to_model


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
    openapi_extra=POD_CREATE_REQUEST_SCHEMA,
)
async def create_pod(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    service: PodService = Depends(get_pod_service),
):
    # Form 데이터를 PodCreateRequest로 파싱
    req = await parse_form_to_model(request, PodCreateRequest, "req")

    # 파일 업로드 처리
    form_data = await request.form()

    # 파일 필드들을 UploadFile 객체로 가져오기
    image = None
    thumbnail = None

    if "image" in form_data:
        image_file = form_data["image"]
        if hasattr(image_file, "filename") and image_file.filename:
            image = image_file

    if "thumbnail" in form_data:
        thumbnail_file = form_data["thumbnail"]
        if hasattr(thumbnail_file, "filename") and thumbnail_file.filename:
            thumbnail = thumbnail_file

    pod = await service.create_pod(
        owner_id=user_id,
        req=req,
        image=image,
        thumbnail=thumbnail,
    )
    if pod is None:
        return BaseResponse.error(
            code=HttpStatus.BAD_REQUEST,
        )
    return BaseResponse.ok(
        data=pod,
        code=HttpStatus.CREATED,
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
    selected_artist_id: int,
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
    selected_artist_id: int,
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
    selected_artist_id: int,
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
    selected_artist_id: int,
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
        return BaseResponse.error(
            code=HttpStatus.NOT_FOUND,
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
    return BaseResponse.ok(code=HttpStatus.NO_CONTENT)
