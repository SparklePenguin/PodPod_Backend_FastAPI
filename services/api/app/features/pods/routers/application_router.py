"""Pod 신청서 라우터"""

from typing import List

from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.service import get_application_use_case
from app.features.pods.schemas import (
    ApplyToPodRequest,
    PodApplDetailDto,
    PodApplDto,
    ReviewApplicationRequest,
)
from app.features.pods.use_cases.application_use_case import ApplicationUseCase
from fastapi import APIRouter, Depends, status

# Pod별 신청서 라우터 (prefix: /pods/{pod_id}/applications)
pod_applications_router = APIRouter()

# 신청서 개별 라우터 (prefix: /applications)
applications_router = APIRouter()


@pod_applications_router.get(
    "",
    response_model=BaseResponse[List[PodApplDto]],
    description="Pod의 신청서 리스트 조회",
)
# MARK: - 파티 신청서 목록 조회
async def get_pod_applications(
    pod_id: int,
    use_case: ApplicationUseCase = Depends(get_application_use_case),
):
    result = await use_case.get_applications_by_pod_id(pod_id, include_hidden=False)
    return BaseResponse.ok(
        data=result,
        message_ko="신청서 목록을 조회했습니다.",
        message_en="Applications retrieved successfully.",
    )


@pod_applications_router.post(
    "",
    response_model=BaseResponse[PodApplDetailDto],
    description="신청서 생성 (파티 참여 신청)",
)
# MARK: - 파티 참여 신청
async def create_application(
    pod_id: int,
    request: ApplyToPodRequest | None = None,
    user_id: int = Depends(get_current_user_id),
    use_case: ApplicationUseCase = Depends(get_application_use_case),
):
    message = request.message if request else None
    result = await use_case.apply_to_pod(pod_id, user_id, message)
    return BaseResponse.ok(
        data=result,
        http_status=status.HTTP_201_CREATED,
        message_ko="파티 참여 신청이 완료되었습니다.",
        message_en="Application created successfully.",
    )


@applications_router.put(
    "/{application_id}/review",
    response_model=BaseResponse[PodApplDetailDto],
    description="신청서 리뷰 등록/수정 (승인/거절)",
)
# MARK: - 신청서 승인/거절
async def review_application(
    application_id: int,
    request: ReviewApplicationRequest,
    user_id: int = Depends(get_current_user_id),
    use_case: ApplicationUseCase = Depends(get_application_use_case),
):
    result = await use_case.review_application(application_id, request.status, user_id)
    return BaseResponse.ok(
        data=result,
        message_ko="신청서가 성공적으로 처리되었습니다.",
        message_en="Application reviewed successfully.",
    )


@applications_router.put(
    "/{application_id}/hide",
    response_model=BaseResponse[bool],
    description="신청서 숨김 처리 (파티장용)",
)
# MARK: - 신청서 숨김 처리
async def hide_application(
    application_id: int,
    current_user_id: int = Depends(get_current_user_id),
    use_case: ApplicationUseCase = Depends(get_application_use_case),
):
    result = await use_case.hide_application(application_id, current_user_id)
    return BaseResponse.ok(
        data=result,
        message_ko="신청서가 성공적으로 숨김 처리되었습니다.",
        message_en="Application hidden successfully.",
    )


@applications_router.delete(
    "/{application_id}",
    response_model=BaseResponse[bool],
    description="신청서 취소 (신청자용)",
)
# MARK: - 신청서 취소
async def cancel_application(
    application_id: int,
    current_user_id: int = Depends(get_current_user_id),
    use_case: ApplicationUseCase = Depends(get_application_use_case),
):
    result = await use_case.cancel_application(application_id, current_user_id)
    return BaseResponse.ok(
        data=result,
        message_ko="신청이 성공적으로 취소되었습니다.",
        message_en="Application cancelled successfully.",
    )
