from app.core.http_status import HttpStatus
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.services.pod.pod_service import PodService
from app.schemas.common import BaseResponse
from app.schemas.pod import PodLikeDto


router = APIRouter()


def get_pod_service(
    db: AsyncSession = Depends(get_db),
) -> PodService:
    return PodService(db)


# - MARK: 좋아요 등록
@router.post(
    "/{pod_id}/likes",
    response_model=BaseResponse[None],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[None],
            "description": "좋아요 등록 성공",
        },
    },
)
async def like_pod(
    pod_id: int,
    user_id: int = Depends(get_current_user_id),
    service: PodService = Depends(get_pod_service),
):
    await service.like_pod(pod_id, user_id)
    return BaseResponse.ok()


# - MARK: 좋아요 취소
@router.delete(
    "/{pod_id}/likes",
    response_model=BaseResponse[None],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[None],
            "description": "좋아요 취소 성공",
        },
    },
)
async def unlike_pod(
    pod_id: int,
    user_id: int = Depends(get_current_user_id),
    service: PodService = Depends(get_pod_service),
):
    await service.unlike_pod(pod_id, user_id)
    return BaseResponse.ok()


# - MARK: 좋아요 상태
@router.get(
    "/{pod_id}/likes",
    response_model=BaseResponse[PodLikeDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PodLikeDto],
            "description": "좋아요 상태 조회 성공",
        },
    },
)
async def like_status(
    pod_id: int,
    user_id: int = Depends(get_current_user_id),
    service: PodService = Depends(get_pod_service),
):
    status = await service.like_status(pod_id, user_id)
    return BaseResponse.ok(data=status)
