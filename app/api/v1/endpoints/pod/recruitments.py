from app.core.http_status import HttpStatus
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.services.pod.pod_service import PodService
from app.services.pod.recruitment_service import RecruitmentService
from app.schemas.common import BaseResponse
from app.schemas.pod.pod_application_dto import PodApplicationDto
from app.schemas.pod.pod_member_dto import PodMemberDto
from app.schemas.follow import SimpleUserDto
from app.models.user import User


router = APIRouter()


# - MARK: 파티 참여 신청 요청 스키마
class ApplyToPodRequest(BaseModel):
    message: Optional[str] = Field(
        default=None, alias="message", description="참여 신청 메시지"
    )

    model_config = {"populate_by_name": True}


# - MARK: 신청서 승인/거절 요청 스키마
class ReviewApplicationRequest(BaseModel):
    status: str = Field(alias="status", description="승인 상태 (approved, rejected)")

    model_config = {"populate_by_name": True}


def get_pod_service(
    db: AsyncSession = Depends(get_db),
) -> PodService:
    return PodService(db)


def get_recruitment_service(
    db: AsyncSession = Depends(get_db),
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
    request: ApplyToPodRequest = None,
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


# - MARK: 파티 참여 신청 취소
@router.delete(
    "/{application_id}",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "파티 참여 신청 취소 성공",
        },
    },
    summary="파티 참여 신청 취소",
    description="특정 신청서를 취소합니다.",
    tags=["recruitments"],
)
async def cancel_apply_to_pod(
    application_id: int,
    user_id: int = Depends(get_current_user_id),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    await recruitment_service.cancel_application_by_id(application_id, user_id)
    return BaseResponse.ok(data={"cancelled": True})


# - MARK: 파티 탈퇴
@router.delete(
    "/pods/{pod_id}/leave",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "파티 탈퇴 성공",
        },
    },
    summary="파티 탈퇴",
    description="참여 중인 파티에서 탈퇴합니다. (파티장은 탈퇴 불가)",
    tags=["recruitments"],
)
async def leave_pod(
    pod_id: int,
    user_id: int = Depends(get_current_user_id),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    success = await recruitment_service.leave_pod(pod_id, user_id)
    return BaseResponse.ok(data={"left": success})


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
    pod_id: int = Query(..., alias="podId", description="파티 ID"),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    applications = (
        await recruitment_service.application_crud.get_applications_by_pod_id(pod_id)
    )

    # PodApplication 모델을 PodApplicationDto로 변환
    from sqlalchemy import select
    from app.models.tendency import UserTendencyResult

    application_dtos = []
    for application in applications:
        user = await recruitment_service.db.get(User, application.user_id)
        reviewer = (
            await recruitment_service.db.get(User, application.reviewed_by)
            if application.reviewed_by
            else None
        )

        # 신청자 성향 타입 조회
        result = await recruitment_service.db.execute(
            select(UserTendencyResult).where(
                UserTendencyResult.user_id == application.user_id
            )
        )
        user_tendency = result.scalar_one_or_none()
        user_tendency_type = user_tendency.tendency_type if user_tendency else None

        # 검토자 성향 타입 조회
        reviewer_tendency_type = None
        if reviewer:
            result = await recruitment_service.db.execute(
                select(UserTendencyResult).where(
                    UserTendencyResult.user_id == application.reviewed_by
                )
            )
            reviewer_tendency = result.scalar_one_or_none()
            reviewer_tendency_type = (
                reviewer_tendency.tendency_type if reviewer_tendency else None
            )

        # SimpleUserDto 생성
        user_dto = SimpleUserDto(
            id=user.id,
            nickname=user.nickname,
            profile_image=user.profile_image,
            intro=user.intro,
            tendency_type=user_tendency_type,
            is_following=False,
        )

        reviewer_dto = None
        if reviewer:
            reviewer_dto = SimpleUserDto(
                id=reviewer.id,
                nickname=reviewer.nickname,
                profile_image=reviewer.profile_image,
                intro=reviewer.intro,
                tendency_type=reviewer_tendency_type,
                is_following=False,
            )

        application_dto = PodApplicationDto(
            id=application.id,
            podId=application.pod_id,
            user=user_dto,
            message=application.message,
            status=application.status,
            appliedAt=application.applied_at,
            reviewedAt=application.reviewed_at,
            reviewedBy=reviewer_dto,
        )
        application_dtos.append(application_dto)

    return BaseResponse.ok(data=application_dtos)
