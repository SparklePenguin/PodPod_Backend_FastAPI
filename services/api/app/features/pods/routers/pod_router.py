from app.common.schemas import BaseResponse, PageDto
from app.core.database import get_session
from app.core.error_codes import get_error_info
from app.core.services.scheduler_service import scheduler
from app.deps.auth import get_current_user_id
from app.deps.service import get_pod_service
from app.features.pods.schemas import PodCreateRequest, PodDetailDto
from app.features.pods.schemas.pod_search_request import PodSearchRequest
from app.features.pods.services.pod_service import PodService
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    Path,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(dependencies=[])


# - MARK: 파티 생성
@router.post(
    "",
    response_model=BaseResponse[PodDetailDto],
    description="파티 생성",
)
async def create_pod(
    title: str = Form(..., description="파티 제목"),
    description: str | None = Form(..., description="파티 설명"),
    sub_categories: list[str] = Form(
        [],
        alias="subCategories",
        description="서브 카테고리 (예: ['EXCHANGE', 'SALE', 'GROUP_PURCHASE'] 등)",
    ),
    capacity: int = Form(..., description="최대 인원수"),
    place: str = Form(..., description="장소명"),
    address: str = Form(..., description="주소"),
    sub_address: str | None = Form(None, alias="subAddress", description="상세 주소"),
    x: float | None = Form(None, description="경도 (longitude)"),
    y: float | None = Form(None, description="위도 (latitude)"),
    # 이제 meetingDate 하나로 UTC datetime을 받음
    meeting_date: str = Form(
        ...,
        alias="meetingDate",
        description="만남 일시 (UTC ISO 8601, 예: 2025-11-20T12:00:00Z)",
    ),
    selected_artist_id: int = Form(
        ..., alias="selectedArtistId", description="선택된 아티스트 ID"
    ),
    images: list[UploadFile] = File(..., description="파티 이미지 리스트"),
    user_id: int = Depends(get_current_user_id),
    service: PodService = Depends(get_pod_service),
):
    # sub_categories는 이미 리스트이므로 그대로 사용
    sub_category_list = sub_categories

    # meetingDate(UTC datetime) 파싱 → date/time 분리
    import logging
    from datetime import date, datetime, time, timezone

    logger = logging.getLogger(__name__)

    normalized = meeting_date.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)

    parsed_meeting_date: date = dt_utc.date()
    parsed_meeting_time: time = dt_utc.time()

    logger.info(
        f"[파티 생성] UTC 시간 저장: 원본={meeting_date}, UTC datetime={dt_utc.isoformat()}, "
        f"date={parsed_meeting_date}, time={parsed_meeting_time}"
    )

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

    pod = await service.create_pod(owner_id=user_id, req=req, images=images)
    return BaseResponse.ok(data=pod, http_status=status.HTTP_201_CREATED)


# - MARK: 인기 파티 조회
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


# - MARK: 마감 직전 파티 조회
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


# - MARK: 우리 만난적 있어요 파티 조회
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


# - MARK: 인기 최고 카테고리 파티 조회
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
    try:
        joined_pods = await pod_service.get_user_joined_pods(
            current_user_id, page, size
        )

        return BaseResponse.ok(
            data=joined_pods,
            http_status=status.HTTP_200_OK,
            message_ko="내가 참여한 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved my joined pods.",
        )
    except Exception:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )


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
    try:
        liked_pods = await pod_service.get_user_liked_pods(current_user_id, page, size)

        return BaseResponse.ok(
            data=liked_pods,
            http_status=status.HTTP_200_OK,
            message_ko="내가 저장한 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved my liked pods.",
        )
    except Exception:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )


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
    try:
        # userId가 제공되지 않으면 현재 사용자 ID 사용
        target_user_id = userId if userId is not None else current_user_id

        # 먼저 해당 사용자가 존재하는지 확인
        from app.core.error_codes import get_error_info
        from app.features.users.services.user_service import UserService

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
            http_status=status.HTTP_200_OK,
            message_ko="사용자가 개설한 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved user's pods.",
        )
    except Exception:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="유저의 파티 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving user's pods.",
            error_key=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


# - MARK: 팟 목록 조회 (검색 포함)
@router.post(
    "/search",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="팟 목록 조회",
)
async def get_pods(
    search_request: PodSearchRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
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
            size=search_request.page_size or 20,
        )

        return BaseResponse.ok(result, message_ko="팟 목록 조회 성공", http_status=200)

    except ValueError as e:
        error_info = get_error_info("INVALID_REQUEST")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="잘못된 날짜 형식입니다.",
            message_en="Invalid date format.",
            error_key=error_info.error_key,
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
            error_key=error_info.error_key,
            error_code=error_info.code,
            dev_note=str(e),
        )


# - MARK: 파티별 후기 목록 조회
@router.get(
    "/{pod_id}/reviews",
    response_model=BaseResponse[PageDto],
    description="특정 파티의 후기 목록 조회",
)
async def get_pod_reviews(
    pod_id: int = Path(..., description="파티 ID"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    db: AsyncSession = Depends(get_session),
):
    """파티별 후기 목록 조회"""
    try:
        from app.features.pods.services.pod_review_service import PodReviewService

        review_service = PodReviewService(db)
        reviews = await review_service.get_reviews_by_pod(pod_id, page, size)

        return BaseResponse.ok(
            data=reviews,
            http_status=status.HTTP_200_OK,
            message_ko="파티 후기 목록을 조회했습니다.",
            message_en="Pod reviews retrieved successfully.",
        )
    except Exception:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="후기 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving reviews.",
            error_key=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


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
    title: str | None = Form(None, description="파티 제목"),
    description: str | None = Form(None, description="파티 설명"),
    sub_categories: list[str | None] = Form(
        None, alias="subCategories", description="서브 카테고리"
    ),
    capacity: int | None = Form(None, description="최대 인원수"),
    place: str | None = Form(None, description="장소명"),
    address: str | None = Form(None, description="주소"),
    sub_address: str | None = Form(None, alias="subAddress", description="상세 주소"),
    x: float | None = Form(None, description="경도 (longitude)"),
    y: float | None = Form(None, description="위도 (latitude)"),
    # 이제 meetingDate 하나로 UTC datetime을 받음
    meeting_date: str | None = Form(
        None,
        alias="meetingDate",
        description="만남 일시 (UTC ISO 8601, 예: 2025-11-20T12:00:00Z)",
    ),
    selected_artist_id: int | None = Form(
        None, alias="selectedArtistId", description="선택된 아티스트 ID"
    ),
    image_orders: str | None = Form(
        None,
        alias="imageOrders",
        description="이미지 순서 JSON 문자열 (기존: {type: 'existing', url: '...'}, 신규: {type: 'new', fileIndex: 0})",
    ),
    new_images: list[UploadFile | None] = File(
        None,
        alias="newImages",
        description="새로 업로드할 이미지 파일 리스트",
    ),
    current_user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    import logging

    logger = logging.getLogger(__name__)

    # 모든 Form 데이터 로깅
    logger.info("[API] 받은 모든 Form 데이터:")
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

    # 날짜와 시간 파싱 (meetingDate: UTC datetime → date/time 분리)
    if meeting_date is not None:
        from datetime import datetime, timezone

        normalized = meeting_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        dt_utc = dt.astimezone(timezone.utc)

        update_fields["meeting_date"] = dt_utc.date()
        update_fields["meeting_time"] = dt_utc.time()

        logger.info(
            f"[파티 수정] UTC 시간 저장: 원본={meeting_date}, UTC datetime={dt_utc.isoformat()}, "
            f"date={update_fields['meeting_date']}, time={update_fields['meeting_time']}"
        )

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
            http_status=status.HTTP_400_BAD_REQUEST,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )

    return BaseResponse.ok(data=updated_pod)


# - MARK: 파티 삭제
@router.delete(
    "/{pod_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="파티 삭제",
)
async def delete_pod(pod_id: int, pod_service: PodService = Depends(get_pod_service)):
    await pod_service.delete_pod(pod_id)
    return BaseResponse.ok(http_status=status.HTTP_204_NO_CONTENT)


# - MARK: 파티 상태 업데이트 (JSON 요청 본문 방식 - 더 RESTful)
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
    if "status" not in request:
        from app.core.error_codes import get_error_info
        error_info = get_error_info("MISSING_STATUS")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=error_info.http_status,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
        )

    status_value = request["status"]
    updated_pod = await pod_service.update_pod_status_by_owner(
        pod_id, status_value, current_user_id
    )
    return BaseResponse.ok(
        data=updated_pod,
        message_ko=f"파티 상태가 {status_value}로 성공적으로 변경되었습니다.",
    )


# - MARK: 파티 멤버 삭제 (토큰 기반)
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
    """파티 멤버 삭제"""
    result = await pod_service.leave_pod(pod_id, user_id, current_user_id)

    if result["is_owner"]:
        message = f"파티장이 나가서 파티가 종료되었습니다. {result['members_removed']}명의 멤버가 함께 나갔습니다."
    else:
        message = "파티에서 성공적으로 나갔습니다."

    return BaseResponse.ok(data=result, message_ko=message)


@router.post(
    "/test-scheduler",
    description="스케줄러 테스트",
)
async def test_scheduler(db: AsyncSession = Depends(get_session)):
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
    description="파티 디버그",
)
async def debug_pods(db: AsyncSession = Depends(get_session)):
    """파티 디버그"""
    from app.features.pods.models.pod import Pod
    from sqlalchemy import select

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
    description="파티 88번 날짜 수정",
)
async def fix_pod88_date(db: AsyncSession = Depends(get_session)):
    """파티 88번 날짜 수정"""
    from datetime import date

    from app.features.pods.models.pod import Pod
    from sqlalchemy import select, update

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
    description="리뷰 알림 테스트",
)
async def test_review_notification(db: AsyncSession = Depends(get_session)):
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
    description="null 알림 정리",
)
async def cleanup_null_notifications(db: AsyncSession = Depends(get_session)):
    """null 알림 정리"""
    from app.features.notifications.models.notification import Notification
    from sqlalchemy import delete

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


@router.post(
    "/cleanup-chat-notifications",
    description="채팅 메시지 알림 정리",
)
async def cleanup_chat_notifications(db: AsyncSession = Depends(get_session)):
    """채팅 메시지 알림 정리"""
    from app.features.notifications.models.notification import Notification
    from sqlalchemy import delete

    try:
        # CHAT_MESSAGE_RECEIVED 알림들 삭제
        delete_query = delete(Notification).where(
            Notification.notification_value == "CHAT_MESSAGE_RECEIVED"
        )
        result = await db.execute(delete_query)
        await db.commit()

        deleted_count = result.rowcount
        return BaseResponse.ok(
            data={"deleted_count": deleted_count},
            message_ko=f"{deleted_count}개의 채팅 메시지 알림이 삭제되었습니다.",
        )
    except Exception as e:
        return BaseResponse.ok(
            data={"error": str(e)}, message_ko=f"채팅 메시지 알림 정리 실패: {e}"
        )


@router.get(
    "/debug-notifications",
    description="알림 디버그",
)
async def debug_notifications(db: AsyncSession = Depends(get_session)):
    from app.features.notifications.models.notification import Notification
    from sqlalchemy import select

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
