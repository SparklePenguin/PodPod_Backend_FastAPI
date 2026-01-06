from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.providers import get_follow_service
from app.features.follow.schemas import (
    FollowInfoDto,
    FollowRequest,
    FollowStatsDto,
)
from app.features.follow.services.follow_service import FollowService
from fastapi import APIRouter, Depends, Path, status

router = APIRouter(prefix="/follow", tags=["follow"])


# - MARK: 사용자 팔로우
@router.post(
    "/", response_model=BaseResponse[FollowInfoDto], description="사용자 팔로우"
)
async def follow_user(
    request: FollowRequest,
    current_user_id: int = Depends(get_current_user_id),
    follow_service: FollowService = Depends(get_follow_service),
):
    follow = await follow_service.follow_user(
        follower_id=current_user_id, following_id=request.following_id
    )

    return BaseResponse.ok(
        data=follow,
        http_status=status.HTTP_201_CREATED,
        message_ko="팔로우가 완료되었습니다.",
        message_en="Successfully followed the user.",
    )


# - MARK: 사용자 팔로우 취소
@router.delete(
    "/{following_id}",
    response_model=BaseResponse[bool],
    description="사용자 팔로우 취소",
)
async def unfollow_user(
    following_id: int = Path(..., description="팔로우 취소할 사용자 ID"),
    current_user_id: int = Depends(get_current_user_id),
    follow_service: FollowService = Depends(get_follow_service),
):
    await follow_service.unfollow_user(
        follower_id=current_user_id, following_id=following_id
    )

    return BaseResponse.ok(
        data=True,
        http_status=status.HTTP_200_OK,
        message_ko="팔로우가 취소되었습니다.",
        message_en="Successfully unfollowed the user.",
    )


# - MARK: 팔로우 통계 조회
@router.get(
    "/stats/{user_id}",
    response_model=BaseResponse[FollowStatsDto],
    description="팔로우 통계 조회",
)
async def get_follow_stats(
    user_id: int = Path(..., description="사용자 ID"),
    current_user_id: int | None = Depends(get_current_user_id),
    follow_service: FollowService = Depends(get_follow_service),
):
    stats = await follow_service.get_follow_stats(
        user_id=user_id, current_user_id=current_user_id
    )

    return BaseResponse.ok(
        data=stats,
        http_status=status.HTTP_200_OK,
        message_ko="팔로우 통계를 조회했습니다.",
        message_en="Successfully retrieved follow statistics.",
    )
