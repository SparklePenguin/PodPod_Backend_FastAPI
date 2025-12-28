from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse
from app.core.database import get_session
from app.core.error_codes import raise_error
from app.core.http_status import HttpStatus
from app.deps.auth import get_current_user_id
from app.features.follow.schemas import SimpleUserDto
from app.features.pods.schemas.pod_application_dto import PodApplicationDto
from app.features.pods.services.pod_service import PodService
from app.features.pods.services.recruitment_service import RecruitmentService
from app.features.users.models import User

router = APIRouter()


# - MARK: 파티 참여 신청 요청 스키마
class ApplyToPodRequest(BaseModel):
    message: Optional[str] = Field(
        default=None, serialization_alias="message", description="참여 신청 메시지"
    )

    model_config = {"populate_by_name": True}


# - MARK: 신청서 승인/거절 요청 스키마
class ReviewApplicationRequest(BaseModel):
    status: str = Field(
        serialization_alias="status", description="승인 상태 (approved, rejected)"
    )

    model_config = {"populate_by_name": True}


def get_pod_service(
    db: AsyncSession = Depends(get_session),
) -> PodService:
    return PodService(db)


def get_recruitment_service(
    db: AsyncSession = Depends(get_session),
) -> RecruitmentService:
    return RecruitmentService(db)


# - MARK: 파티 참여 신청
@router.post(
    "/{pod_id}",
    response_model=BaseResponse[PodApplicationDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PodApplicationDto],
            "description": "파티 참여 신청 성공",
        },
    },
    summary="파티 참여 신청",
    description="특정 파티에 참여를 신청합니다. 메시지를 포함할 수 있습니다.",
    tags=["recruitments"],
)
async def apply_to_pod(
    pod_id: int,
    request: Optional[ApplyToPodRequest] = None,
    user_id: int = Depends(get_current_user_id),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    message = request.message if request else None
    application_dto = await recruitment_service.apply_to_pod(pod_id, user_id, message)
    return BaseResponse.ok(data=application_dto)


# - MARK: 신청서 승인/거절
@router.put(
    "/{application_id}",
    response_model=BaseResponse[PodApplicationDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PodApplicationDto],
            "description": "신청서 승인/거절 성공",
        },
    },
    summary="신청서 승인/거절",
    description="파티 참여 신청서를 승인하거나 거절합니다.",
    tags=["recruitments"],
)
async def review_application(
    application_id: int,
    request: ReviewApplicationRequest,
    user_id: int = Depends(get_current_user_id),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    application_dto = await recruitment_service.review_application(
        application_id, request.status, user_id
    )
    return BaseResponse.ok(data=application_dto)


# - MARK: 파티 참여 신청서 처리 (파티장: 숨김, 신청자: 취소)
@router.delete(
    "/{application_id}",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "신청서 처리 성공",
        },
        HttpStatus.NOT_FOUND: {
            "model": BaseResponse[None],
            "description": "신청서를 찾을 수 없음",
        },
        HttpStatus.FORBIDDEN: {
            "model": BaseResponse[None],
            "description": "권한 없음 (파티장 또는 신청자가 아님)",
        },
    },
    summary="파티 참여 신청서 처리",
    description="파티장이면 신청서를 숨김 처리하고, 신청자면 신청을 취소합니다.",
    tags=["recruitments"],
)
async def handle_application(
    application_id: int,
    current_user_id: int = Depends(get_current_user_id),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    """파티장: 신청서 숨김 처리, 신청자: 신청 취소"""
    result = await recruitment_service.handle_application_by_user_role(
        application_id, current_user_id
    )

    if result is None:
        raise_error("APPLICATION_HANDLE_FAILED")

    # 타입 체커를 위해 명시적으로 dict임을 보장
    assert result is not None, "result should not be None after check"
    result_dict: dict = result

    return BaseResponse.ok(
        data=result_dict,
        message_ko=result_dict["message"],
    )


# - MARK: 파티 참여 신청 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[List[PodApplicationDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[List[PodApplicationDto]],
            "description": "파티 참여 신청 목록 조회 성공",
        },
    },
    summary="파티 참여 신청 목록 조회",
    description="특정 파티에 대한 참여 신청서 목록을 조회합니다.",
    tags=["recruitments"],
)
async def get_apply_to_pod_list(
    pod_id: int = Query(..., serialization_alias="podId", description="파티 ID"),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    applications = (
        await recruitment_service.application_crud.get_applications_by_pod_id(
            pod_id, include_hidden=False
        )
    )

    # PodApplication 모델을 PodApplicationDto로 변환
    from sqlalchemy import select

    from app.features.tendencies.models.tendency import UserTendencyResult

    application_dtos = []
    for application in applications:
        user_id_value = getattr(application, "user_id")
        user = await recruitment_service.db.get(User, user_id_value)
        reviewed_by_value = getattr(application, "reviewed_by", None)
        reviewer = (
            await recruitment_service.db.get(User, reviewed_by_value)
            if reviewed_by_value
            else None
        )

        # 신청자 성향 타입 조회
        result = await recruitment_service.db.execute(
            select(UserTendencyResult).where(
                UserTendencyResult.user_id == user_id_value
            )
        )
        user_tendency = result.scalar_one_or_none()
        user_tendency_type = (
            getattr(user_tendency, "tendency_type", None) if user_tendency else None
        )

        # 검토자 성향 타입 조회
        reviewer_tendency_type = None
        if reviewer:
            result = await recruitment_service.db.execute(
                select(UserTendencyResult).where(
                    UserTendencyResult.user_id == reviewed_by_value
                )
            )
            reviewer_tendency = result.scalar_one_or_none()
            reviewer_tendency_type = (
                getattr(reviewer_tendency, "tendency_type", None)
                if reviewer_tendency
                else None
            )

        # SimpleUserDto 생성
        user_dto = SimpleUserDto(
            id=getattr(user, "id"),
            nickname=getattr(user, "nickname"),
            profile_image=getattr(user, "profile_image"),
            intro=getattr(user, "intro"),
            tendency_type=user_tendency_type or "",
            is_following=False,
        )

        reviewer_dto = None
        if reviewer:
            reviewer_dto = SimpleUserDto(
                id=getattr(reviewer, "id"),
                nickname=getattr(reviewer, "nickname"),
                profile_image=getattr(reviewer, "profile_image"),
                intro=getattr(reviewer, "intro"),
                tendency_type=reviewer_tendency_type or "",
                is_following=False,
            )

        application_dto = PodApplicationDto(
            id=getattr(application, "id"),
            podId=getattr(application, "pod_id"),
            user=user_dto,
            message=getattr(application, "message"),
            status=getattr(application, "status"),
            appliedAt=getattr(application, "applied_at"),
            reviewedAt=getattr(application, "reviewed_at"),
            reviewedBy=reviewer_dto,
        )
        application_dtos.append(application_dto)

    return BaseResponse.ok(data=application_dtos)
