from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.service import get_follow_service
from app.features.follow.exceptions import FollowNotFoundException
from app.features.follow.schemas import (
    FollowInfoDto,
    FollowNotificationStatusDto,
    FollowNotificationUpdateRequest,
    FollowRequest,
    FollowStatsDto,
)
from app.features.follow.services.follow_service import FollowService
from app.features.pods.schemas import PodDetailDto
from fastapi import APIRouter, Depends, Path, Query, status

router = APIRouter()


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
        http_status=status.HTTP_CREATED,
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


# - MARK: 팔로우하는 사용자들이 만든 파티 목록 조회
@router.get(
    "/pods",
    response_model=BaseResponse[PageDto[PodDetailDto]],
    description="팔로우하는 사용자들이 만든 파티 목록 조회",
)
async def get_following_users_pods(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    follow_service: FollowService = Depends(get_follow_service),
):
    pods = await follow_service.get_following_pods(
        user_id=current_user_id, page=page, size=size
    )

    return BaseResponse.ok(
        data=pods,
        http_status=status.HTTP_200_OK,
        message_ko="팔로우하는 사용자의 파티 목록을 조회했습니다.",
        message_en="Successfully retrieved following users' pods.",
    )


# - MARK: 특정 팔로우한 유저의 알림 설정 상태 조회
@router.get(
    "/notification/{following_id}",
    response_model=BaseResponse[FollowNotificationStatusDto],
    description="특정 팔로우한 유저의 알림 설정 상태 조회",
)
async def get_notification_status(
    following_id: int = Path(..., description="팔로우한 사용자 ID"),
    current_user_id: int = Depends(get_current_user_id),
    follow_service: FollowService = Depends(get_follow_service),
):
    notification_status = await follow_service.get_notification_status(
        follower_id=current_user_id, following_id=following_id
    )

    if not notification_status:
        raise FollowNotFoundException(current_user_id, following_id)

    return BaseResponse.ok(
        data=notification_status,
        http_status=status.HTTP_200_OK,
        message_ko="알림 설정 상태를 조회했습니다.",
        message_en="Successfully retrieved notification status.",
    )


# - MARK: 특정 팔로우한 유저의 알림 설정 변경
@router.put(
    "/notification",
    response_model=BaseResponse[FollowNotificationStatusDto],
    description="특정 팔로우한 유저의 알림 설정 변경",
)
async def update_notification_status(
    request: FollowNotificationUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    follow_service: FollowService = Depends(get_follow_service),
):
    notification_status = await follow_service.update_notification_status(
        follower_id=current_user_id,
        following_id=request.following_id,
        notification_enabled=request.notification_enabled,
    )

    if not notification_status:
        raise FollowNotFoundException(current_user_id, request.following_id)

    return BaseResponse.ok(
        data=notification_status,
        http_status=status.HTTP_200_OK,
        message_ko="알림 설정이 변경되었습니다.",
        message_en="Successfully updated notification status.",
    )
