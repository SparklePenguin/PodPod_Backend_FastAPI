"""Pod 후기 라우터"""

from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.providers import get_review_use_case
from app.features.pods.schemas import (
    PodReviewCreateRequest,
    PodReviewDto,
    PodReviewUpdateRequest,
)
from app.features.pods.use_cases.review_use_case import ReviewUseCase
from fastapi import APIRouter, Body, Depends, Path, Query, status

# Pod별 후기 라우터 (prefix: /pods/{pod_id}/reviews)
pod_reviews_router = APIRouter(prefix="/pods/{pod_id}/reviews", tags=["reviews"])

# 개별 후기 라우터 (prefix: /reviews)
reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])


# MARK: - Pod별 후기 엔드포인트
@pod_reviews_router.get(
    "",
    response_model=BaseResponse[PageDto[PodReviewDto]],
    description="파티별 후기 목록 조회",
)
async def get_pod_reviews(
    pod_id: int,
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    use_case: ReviewUseCase = Depends(get_review_use_case),
):
    """파티별 후기 목록 조회"""
    reviews = await use_case.get_reviews_by_pod(pod_id, page, size)
    return BaseResponse.ok(
        data=reviews,
        message_ko="파티 후기 목록을 조회했습니다.",
        message_en="Pod reviews retrieved successfully.",
    )


# MARK: - 후기 생성
@pod_reviews_router.post(
    "",
    response_model=BaseResponse[PodReviewDto],
    description="후기 생성",
)
async def create_pod_review(
    pod_id: int,
    request: PodReviewCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    use_case: ReviewUseCase = Depends(get_review_use_case),
):
    """후기 생성"""
    review = await use_case.create_review(current_user_id, request)
    return BaseResponse.ok(
        data=review,
        http_status=status.HTTP_201_CREATED,
        message_ko="후기가 성공적으로 작성되었습니다.",
        message_en="Review created successfully.",
    )


# MARK: - 개별 후기 엔드포인트
# MARK: - 후기 타입 목록 조회
@reviews_router.get(
    "/types",
    response_model=BaseResponse[dict],
    description="후기 조회 가능한 타입 목록",
)
async def get_review_types():
    """사용 가능한 후기 조회 타입 목록"""
    types = {
        "types": [
            {
                "value": "written",
                "labelKo": "작성한 후기",
                "labelEn": "Written Reviews",
                "descriptionKo": "내가 작성한 후기 목록",
                "descriptionEn": "List of reviews I wrote",
            },
            {
                "value": "received",
                "labelKo": "받은 후기",
                "labelEn": "Received Reviews",
                "descriptionKo": "내가 받은 후기 목록",
                "descriptionEn": "List of reviews I received",
            },
        ]
    }
    return BaseResponse.ok(
        data=types,
        message_ko="후기 조회 타입 목록을 조회했습니다.",
        message_en="Successfully retrieved review types.",
    )


# MARK: - 후기 목록 조회 (통합)
@reviews_router.get(
    "",
    response_model=BaseResponse[PageDto[PodReviewDto]],
    description="후기 목록 조회 (type: written, received)",
)
async def get_reviews(
    type: str = Query(
        ...,
        description="후기 타입: written(작성한), received(받은)",
        regex="^(written|received)$",
    ),
    userId: int | None = Query(
        None,
        alias="userId",
        description="조회할 사용자 ID (없으면 현재 사용자)",
    ),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    use_case: ReviewUseCase = Depends(get_review_use_case),
):
    """후기 목록 조회"""
    target_user_id = userId if userId is not None else current_user_id
    
    if type == "written":
        reviews = await use_case.get_reviews_by_user(target_user_id, page, size)
        message_ko = "사용자가 작성한 후기 목록을 조회했습니다."
        message_en = "User written reviews retrieved successfully."
    elif type == "received":
        reviews = await use_case.get_reviews_received_by_user(target_user_id, page, size)
        message_ko = "사용자가 받은 후기 목록을 조회했습니다."
        message_en = "User received reviews retrieved successfully."
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid type. Must be one of: written, received",
        )
    
    return BaseResponse.ok(data=reviews, message_ko=message_ko, message_en=message_en)


# MARK: - 후기 조회
@reviews_router.get(
    "/{review_id}",
    response_model=BaseResponse[PodReviewDto],
    description="후기 조회",
)
async def get_review(
    review_id: int = Path(..., description="후기 ID"),
    use_case: ReviewUseCase = Depends(get_review_use_case),
):
    """후기 조회"""
    review = await use_case.get_review_by_id(review_id)
    return BaseResponse.ok(
        data=review,
        message_ko="후기를 조회했습니다.",
        message_en="Review retrieved successfully.",
    )


# MARK: - 후기 수정
@reviews_router.put(
    "/{review_id}",
    response_model=BaseResponse[PodReviewDto],
    description="후기 수정",
)
async def update_review(
    review_id: int = Path(..., description="후기 ID"),
    request: PodReviewUpdateRequest = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    use_case: ReviewUseCase = Depends(get_review_use_case),
):
    """후기 수정"""
    review = await use_case.update_review(review_id, current_user_id, request)
    return BaseResponse.ok(
        data=review,
        message_ko="후기가 성공적으로 수정되었습니다.",
        message_en="Review updated successfully.",
    )


# MARK: - 후기 삭제
@reviews_router.delete(
    "/{review_id}",
    response_model=BaseResponse[bool],
    description="후기 삭제",
)
async def delete_review(
    review_id: int = Path(..., description="후기 ID"),
    current_user_id: int = Depends(get_current_user_id),
    use_case: ReviewUseCase = Depends(get_review_use_case),
):
    """후기 삭제"""
    result = await use_case.delete_review(review_id, current_user_id)
    return BaseResponse.ok(
        data=result,
        message_ko="후기가 성공적으로 삭제되었습니다.",
        message_en="Review deleted successfully.",
    )


