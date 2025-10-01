from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.services.pod_review_service import PodReviewService
from app.schemas.pod_review import (
    PodReviewCreateRequest,
    PodReviewUpdateRequest,
    PodReviewDto,
)
from app.schemas.common import PageDto, BaseResponse
from app.core.http_status import HttpStatus
from app.core.error_codes import get_error_info

router = APIRouter()


@router.post(
    "/",
    response_model=BaseResponse[PodReviewDto],
    summary="후기 생성",
    description="새로운 파티 후기를 작성합니다.",
    responses={
        201: {
            "description": "후기 생성 성공",
        },
        400: {
            "description": "이미 후기를 작성했거나 잘못된 요청",
        },
    },
)
async def create_review(
    request: PodReviewCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """후기 생성"""
    try:
        review_service = PodReviewService(db)
        review = await review_service.create_review(current_user_id, request)

        if not review:
            error_info = get_error_info("INTERNAL_SERVER_ERROR")
            return BaseResponse(
                data=None,
                http_status=error_info.http_status,
                message_ko="후기 생성에 실패했습니다.",
                message_en="Failed to create review.",
                error=error_info.error_key,
                error_code=error_info.code,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=review,
            http_status=HttpStatus.CREATED,
            message_ko="후기가 성공적으로 작성되었습니다.",
            message_en="Review created successfully.",
        )
    except ValueError as e:
        return BaseResponse(
            data=None,
            http_status=400,
            message_ko=str(e),
            message_en="Bad request.",
            error="BAD_REQUEST",
            error_code=4000,
            dev_note=None,
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="후기 생성 중 오류가 발생했습니다.",
            message_en="An error occurred while creating review.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.get(
    "/{review_id}",
    response_model=BaseResponse[PodReviewDto],
    summary="후기 조회",
    description="특정 후기를 조회합니다.",
    responses={
        200: {
            "description": "후기 조회 성공",
        },
        404: {
            "description": "후기를 찾을 수 없음",
        },
    },
)
async def get_review(
    review_id: int = Path(..., alias="reviewId", description="후기 ID"),
    db: AsyncSession = Depends(get_db),
):
    """후기 조회"""
    try:
        review_service = PodReviewService(db)
        review = await review_service.get_review_by_id(review_id)

        if not review:
            error_info = get_error_info("NOT_FOUND")
            return BaseResponse(
                data=None,
                http_status=error_info.http_status,
                message_ko="후기를 찾을 수 없습니다.",
                message_en="Review not found.",
                error=error_info.error_key,
                error_code=error_info.code,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=review,
            http_status=HttpStatus.OK,
            message_ko="후기를 조회했습니다.",
            message_en="Review retrieved successfully.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="후기 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving review.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.get(
    "/pod/{pod_id}",
    response_model=BaseResponse[PageDto[PodReviewDto]],
    summary="파티별 후기 목록 조회",
    description="특정 파티의 후기 목록을 페이지네이션으로 조회합니다.",
    responses={
        200: {
            "description": "후기 목록 조회 성공",
        },
    },
)
async def get_reviews_by_pod(
    pod_id: int = Path(..., alias="podId", description="파티 ID"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: AsyncSession = Depends(get_db),
):
    """파티별 후기 목록 조회"""
    try:
        review_service = PodReviewService(db)
        reviews = await review_service.get_reviews_by_pod(pod_id, page, size)

        return BaseResponse.ok(
            data=reviews,
            http_status=HttpStatus.OK,
            message_ko="파티 후기 목록을 조회했습니다.",
            message_en="Pod reviews retrieved successfully.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="후기 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving reviews.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.get(
    "/user/{user_id}",
    response_model=BaseResponse[PageDto[PodReviewDto]],
    summary="사용자별 후기 목록 조회",
    description="특정 사용자가 작성한 후기 목록을 페이지네이션으로 조회합니다.",
    responses={
        200: {
            "description": "후기 목록 조회 성공",
        },
    },
)
async def get_reviews_by_user(
    user_id: int = Path(..., alias="userId", description="사용자 ID"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: AsyncSession = Depends(get_db),
):
    """사용자별 후기 목록 조회"""
    try:
        review_service = PodReviewService(db)
        reviews = await review_service.get_reviews_by_user(user_id, page, size)

        return BaseResponse.ok(
            data=reviews,
            http_status=HttpStatus.OK,
            message_ko="사용자 후기 목록을 조회했습니다.",
            message_en="User reviews retrieved successfully.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="후기 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving reviews.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.put(
    "/{review_id}",
    response_model=BaseResponse[PodReviewDto],
    summary="후기 수정",
    description="본인이 작성한 후기를 수정합니다.",
    responses={
        200: {
            "description": "후기 수정 성공",
        },
        400: {
            "description": "권한 없음 또는 잘못된 요청",
        },
        404: {
            "description": "후기를 찾을 수 없음",
        },
    },
)
async def update_review(
    review_id: int = Path(..., alias="reviewId", description="후기 ID"),
    request: PodReviewUpdateRequest = ...,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """후기 수정"""
    try:
        review_service = PodReviewService(db)
        review = await review_service.update_review(review_id, current_user_id, request)

        if not review:
            error_info = get_error_info("INTERNAL_SERVER_ERROR")
            return BaseResponse(
                data=None,
                http_status=error_info.http_status,
                message_ko="후기 수정에 실패했습니다.",
                message_en="Failed to update review.",
                error=error_info.error_key,
                error_code=error_info.code,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=review,
            http_status=HttpStatus.OK,
            message_ko="후기가 성공적으로 수정되었습니다.",
            message_en="Review updated successfully.",
        )
    except ValueError as e:
        return BaseResponse(
            data=None,
            http_status=400,
            message_ko=str(e),
            message_en="Bad request.",
            error="BAD_REQUEST",
            error_code=4000,
            dev_note=None,
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="후기 수정 중 오류가 발생했습니다.",
            message_en="An error occurred while updating review.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.delete(
    "/{review_id}",
    response_model=BaseResponse[bool],
    summary="후기 삭제",
    description="본인이 작성한 후기를 삭제합니다.",
    responses={
        200: {
            "description": "후기 삭제 성공",
        },
        400: {
            "description": "권한 없음",
        },
        404: {
            "description": "후기를 찾을 수 없음",
        },
    },
)
async def delete_review(
    review_id: int = Path(..., alias="reviewId", description="후기 ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """후기 삭제"""
    try:
        review_service = PodReviewService(db)
        success = await review_service.delete_review(review_id, current_user_id)

        if not success:
            error_info = get_error_info("INTERNAL_SERVER_ERROR")
            return BaseResponse(
                data=None,
                http_status=error_info.http_status,
                message_ko="후기 삭제에 실패했습니다.",
                message_en="Failed to delete review.",
                error=error_info.error_key,
                error_code=error_info.code,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=True,
            http_status=HttpStatus.OK,
            message_ko="후기가 성공적으로 삭제되었습니다.",
            message_en="Review deleted successfully.",
        )
    except ValueError as e:
        return BaseResponse(
            data=None,
            http_status=400,
            message_ko=str(e),
            message_en="Bad request.",
            error="BAD_REQUEST",
            error_code=4000,
            dev_note=None,
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="후기 삭제 중 오류가 발생했습니다.",
            message_en="An error occurred while deleting review.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )
