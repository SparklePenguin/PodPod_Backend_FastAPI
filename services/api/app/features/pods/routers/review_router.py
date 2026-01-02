from app.common.schemas import BaseResponse, PageDto
from app.core.error_codes import get_error_info
from app.deps.auth import get_current_user_id
from app.deps.service import get_pod_review_service
from app.features.pods.schemas import (
    PodReviewCreateRequest,
    PodReviewDto,
    PodReviewUpdateRequest,
)
from app.features.pods.services.pod_review_service import PodReviewService
from fastapi import APIRouter, Body, Depends, Path, Query, status

router = APIRouter()


@router.post(
    "",
    response_model=BaseResponse[PodReviewDto],
    description="후기 생성",
)
# - MARK: 후기 생성
async def create_review(
    request: PodReviewCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: PodReviewService = Depends(get_pod_review_service),
):
    """후기 생성"""
    review = await service.create_review(current_user_id, request)
    return BaseResponse.ok(
        data=review,
        http_status=status.HTTP_201_CREATED,
        message_ko="후기가 성공적으로 작성되었습니다.",
        message_en="Review created successfully.",
    )


# - MARK: 후기 조회
@router.get(
    "/{review_id}",
    response_model=BaseResponse[PodReviewDto],
    description="후기 조회",
)
async def get_review(
    review_id: int = Path(..., description="후기 ID"),
    service: PodReviewService = Depends(get_pod_review_service),
):
    """후기 조회"""
    review = await service.get_review_by_id(review_id)
    return BaseResponse.ok(
        data=review,
        http_status=status.HTTP_200_OK,
        message_ko="후기를 조회했습니다.",
        message_en="Review retrieved successfully.",
    )


# - MARK: 파티별 후기 목록 조회
@router.get(
    "",
    response_model=BaseResponse[PageDto[PodReviewDto]],
    description="후기 목록 조회 (파티 ID로 필터링 가능)",
)
async def get_reviews(
    pod_id: int = Query(..., alias="pod", description="파티 ID (필터링용)"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, description="페이지 크기 (1~100)"
    ),
    service: PodReviewService = Depends(get_pod_review_service),
):
    """후기 목록 조회 (파티 ID로 필터링)"""
    try:
        reviews = await service.get_reviews_by_pod(pod_id, page, size)

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


# - MARK: 후기 수정
@router.put(
    "/{review_id}",
    response_model=BaseResponse[PodReviewDto],
    description="후기 수정",
)
async def update_review(
    review_id: int = Path(..., description="후기 ID"),
    request: PodReviewUpdateRequest = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    service: PodReviewService = Depends(get_pod_review_service),
):
    """후기 수정"""
    review = await service.update_review(review_id, current_user_id, request)
    return BaseResponse.ok(
        data=review,
        http_status=status.HTTP_200_OK,
        message_ko="후기가 성공적으로 수정되었습니다.",
        message_en="Review updated successfully.",
    )


# - MARK: 후기 삭제
@router.delete(
    "/{review_id}",
    response_model=BaseResponse[bool],
    description="후기 삭제",
)
async def delete_review(
    review_id: int = Path(..., description="후기 ID"),
    current_user_id: int = Depends(get_current_user_id),
    service: PodReviewService = Depends(get_pod_review_service),
):
    """후기 삭제"""
    await service.delete_review(review_id, current_user_id)
    return BaseResponse.ok(
        data=True,
        http_status=status.HTTP_200_OK,
        message_ko="후기가 성공적으로 삭제되었습니다.",
        message_en="Review deleted successfully.",
    )


# - MARK: 사용자가 작성한 후기 목록 조회
@router.get(
    "/user/written",
    response_model=BaseResponse[PageDto[PodReviewDto]],
    description="사용자가 작성한 후기 목록 조회",
)
async def get_user_written_reviews(
    user_id: int | None = Query(
        None,
        alias="userId",
        description="조회할 사용자 ID (없으면 현재 사용자)",
    ),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, description="페이지 크기 (1~100)"
    ),
    current_user_id: int = Depends(get_current_user_id),
    service: PodReviewService = Depends(get_pod_review_service),
):
    """사용자가 작성한 후기 목록 조회"""
    target_user_id = user_id if user_id is not None else current_user_id
    reviews = await service.get_reviews_by_user(target_user_id, page, size)
    return BaseResponse.ok(
        data=reviews,
        http_status=status.HTTP_200_OK,
        message_ko="사용자가 작성한 후기 목록을 조회했습니다.",
        message_en="User written reviews retrieved successfully.",
    )


# - MARK: 사용자가 받은 후기 목록 조회
@router.get(
    "/user/received",
    response_model=BaseResponse[PageDto[PodReviewDto]],
    description="사용자가 받은 후기 목록 조회",
)
async def get_user_received_reviews(
    user_id: int | None = Query(
        None,
        alias="userId",
        description="조회할 사용자 ID (없으면 현재 사용자)",
    ),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, description="페이지 크기 (1~100)"
    ),
    current_user_id: int = Depends(get_current_user_id),
    service: PodReviewService = Depends(get_pod_review_service),
):
    """사용자가 받은 후기 목록 조회"""
    target_user_id = user_id if user_id is not None else current_user_id
    reviews = await service.get_reviews_received_by_user(
        target_user_id, page, size
    )
    return BaseResponse.ok(
        data=reviews,
        http_status=status.HTTP_200_OK,
        message_ko="사용자가 받은 후기 목록을 조회했습니다.",
        message_en="User received reviews retrieved successfully.",
    )
