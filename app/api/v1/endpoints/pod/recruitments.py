from app.core.http_status import HttpStatus
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.services.pod.pod_service import PodService
from app.schemas.common import BaseResponse


router = APIRouter()


def get_pod_service(
    db: AsyncSession = Depends(get_db),
) -> PodService:
    return PodService(db)


# - MARK: 파티 참여 신청
@router.post(
    "/",
    response_model=BaseResponse[None],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[None],
            "description": "파티 참여 신청 성공",
        },
    },
)
async def apply_to_pod(
    pod_id: int,
    user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    await pod_service.apply_to_pod(pod_id, user_id)
    return BaseResponse.ok()


# - MARK: 파티 참여 신청 취소
@router.delete(
    "/",
    status_code=HttpStatus.NO_CONTENT,
)
async def cancel_apply_to_pod(
    pod_id: int,
    user_id: int = Depends(get_current_user_id),
    pod_service: PodService = Depends(get_pod_service),
):
    await pod_service.crud.remove_member(pod_id, user_id)


# - MARK: 파티 참여 신청 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[None],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[None],
            "description": "파티 참여 신청 목록 조회 성공",
        },
    },
)
async def get_apply_to_pod_list(
    pod_id: int,
    pod_service: PodService = Depends(get_pod_service),
):
    apply_to_pod_list = await pod_service.crud.list_members(pod_id)
    return BaseResponse.ok(
        code=HttpStatus.OK,
        data=apply_to_pod_list,
    )
