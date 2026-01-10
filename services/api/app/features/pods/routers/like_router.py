from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.providers import get_like_use_case
from app.features.pods.schemas import PodLikeDto
from app.features.pods.use_cases.like_use_case import LikeUseCase
from fastapi import APIRouter, Depends, Path

router = APIRouter(prefix="/pods", tags=["pods"])


# MARK: - 좋아요 등록
@router.post(
    "/{pod_id}/likes",
    response_model=BaseResponse[None],
)
async def like_pod(
    pod_id: int = Path(..., description="파티 ID"),
    user_id: int = Depends(get_current_user_id),
    use_case: LikeUseCase = Depends(get_like_use_case),
):
    await use_case.like_pod(pod_id, user_id)
    return BaseResponse.ok()


# MARK: - 좋아요 취소
@router.delete(
    "/{pod_id}/likes",
    response_model=BaseResponse[None],
)
async def unlike_pod(
    pod_id: int = Path(..., description="파티 ID"),
    user_id: int = Depends(get_current_user_id),
    use_case: LikeUseCase = Depends(get_like_use_case),
):
    await use_case.unlike_pod(pod_id, user_id)
    return BaseResponse.ok()


# MARK: - 좋아요 상태
@router.get(
    "/{pod_id}/likes",
    response_model=BaseResponse[PodLikeDto],
)
async def like_status(
    pod_id: int = Path(..., description="파티 ID"),
    user_id: int = Depends(get_current_user_id),
    use_case: LikeUseCase = Depends(get_like_use_case),
):
    result = await use_case.like_status(pod_id, user_id)
    return BaseResponse.ok(data=result)
