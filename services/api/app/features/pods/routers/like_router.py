from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.service import get_pod_like_service
from app.features.pods.schemas import PodLikeDto
from app.features.pods.services.pod_like_service import PodLikeService
from fastapi import APIRouter, Depends, Path

router = APIRouter()


# - MARK: 좋아요 등록
@router.post(
    "/{pod_id}/likes",
    response_model=BaseResponse[None],
)
async def like_pod(
    pod_id: int = Path(..., description="파티 ID"),
    user_id: int = Depends(get_current_user_id),
    service: PodLikeService = Depends(get_pod_like_service),
):
    result = await service.like_pod(pod_id, user_id)
    return BaseResponse.ok(data=result)


# - MARK: 좋아요 취소
@router.delete(
    "/{pod_id}/likes",
    response_model=BaseResponse[None],
)
async def unlike_pod(
    pod_id: int = Path(..., description="파티 ID"),
    user_id: int = Depends(get_current_user_id),
    service: PodLikeService = Depends(get_pod_like_service),
):
    result = await service.unlike_pod(pod_id, user_id)
    return BaseResponse.ok(data=result)


# - MARK: 좋아요 상태
@router.get(
    "/{pod_id}/likes",
    response_model=BaseResponse[PodLikeDto],
)
async def like_status(
    pod_id: int = Path(..., description="파티 ID"),
    user_id: int = Depends(get_current_user_id),
    service: PodLikeService = Depends(get_pod_like_service),
):
    result = await service.like_status(pod_id, user_id)
    return BaseResponse.ok(data=result)
