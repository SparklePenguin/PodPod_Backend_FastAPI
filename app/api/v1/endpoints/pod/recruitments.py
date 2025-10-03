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
    "/",
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
    pod_id: int = Query(..., alias="podId", description="파티 ID"),
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
    "/",
    status_code=HttpStatus.NO_CONTENT,
    responses={
        HttpStatus.NO_CONTENT: {
            "description": "파티 참여 신청 취소 성공",
        },
    },
    summary="파티 참여 신청 취소",
    description="특정 파티에 대한 참여 신청을 취소합니다.",
    tags=["recruitments"],
)
async def cancel_apply_to_pod(
    pod_id: int = Query(..., alias="podId", description="파티 ID"),
    user_id: int = Depends(get_current_user_id),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    await recruitment_service.crud.remove_member(pod_id, user_id)


# - MARK: 파티 참여 신청 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[List[PodMemberDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[List[PodMemberDto]],
            "description": "파티 참여 신청 목록 조회 성공",
        },
    },
    summary="파티 참여 신청 목록 조회",
    description="특정 파티에 대한 참여 신청자 목록을 조회합니다.",
    tags=["recruitments"],
)
async def get_apply_to_pod_list(
    pod_id: int = Query(..., alias="podId", description="파티 ID"),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
):
    apply_to_pod_list = await recruitment_service.crud.list_members(pod_id)
    # PodMember 모델을 PodMemberDto로 변환
    pod_member_dtos = []
    for member in apply_to_pod_list:
        simple_user = SimpleUserDto(
            id=member.user.id,
            nickname=member.user.nickname,
            profile_image=member.user.profile_image,
            intro=member.user.intro,
            tendency_type=member.user.tendency_type,
            is_following=False,  # 기본값으로 설정
        )
        pod_member_dto = PodMemberDto(
            id=member.id,
            user=simple_user,
            role=member.role,
            message=member.message,
            created_at=member.created_at,
        )
        pod_member_dtos.append(pod_member_dto)

    return BaseResponse.ok(
        data=pod_member_dtos,
    )
