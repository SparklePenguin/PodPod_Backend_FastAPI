from fastapi import (
    Body,
    Depends,
)

from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.providers import (
    get_follow_use_case,
)
from app.features.follow.exceptions import FollowNotFoundException
from app.features.follow.use_cases.follow_use_case import FollowUseCase
from app.features.users.routers._base import UserFollowingsController


class UserFollowingsRouter:

    @staticmethod
    @UserFollowingsController.ROUTER.get(
        f"{UserFollowingsController.PREFIX}/" + "{following_id}/mute",
        response_model=BaseResponse[dict],
        summary="팔로우한 사용자 알림 음소거 설정 조회",
        description="팔로우한 사용자의 알림 음소거 설정 조회",
    )
    async def get_following_mute_status(
            following_id: int,
            current_user_id: int = Depends(get_current_user_id),
            follow_use_case: FollowUseCase = Depends(get_follow_use_case),
    ):
        """팔로우한 사용자의 알림 음소거 설정 조회"""
        notification_status = await follow_use_case.get_notification_status(
            follower_id=current_user_id, following_id=following_id
        )

        if not notification_status:
            raise FollowNotFoundException(current_user_id, following_id)

        # notification_enabled가 false면 muted는 true
        muted = not notification_status.notification_enabled

        return BaseResponse.ok(
            data={"muted": muted},
            message_ko="알림 음소거 설정을 조회했습니다.",
            message_en="Successfully retrieved mute status.",
        )

    @staticmethod
    @UserFollowingsController.ROUTER.put(
        f"{UserFollowingsController.PREFIX}/" + "{following_id}/mute",
        response_model=BaseResponse[dict],
        summary=" 팔로우한 사용자 알림 음소거 설정 변경",
        description="팔로우한 사용자의 알림 음소거 설정 변경",
    )
    async def update_following_mute_status(
            following_id: int,
            request: dict = Body(..., description="음소거 설정 요청"),
            current_user_id: int = Depends(get_current_user_id),
            follow_use_case: FollowUseCase = Depends(get_follow_use_case),
    ):
        """팔로우한 사용자의 알림 음소거 설정 변경"""
        muted = request.get("muted", False)

        # muted가 true면 notification_enabled는 false
        notification_enabled = not muted

        notification_status = await follow_use_case.update_notification_status(
            follower_id=current_user_id,
            following_id=following_id,
            notification_enabled=notification_enabled,
        )

        if not notification_status:
            raise FollowNotFoundException(current_user_id, following_id)

        return BaseResponse.ok(
            data={"muted": muted},
            message_ko="알림 음소거 설정이 변경되었습니다.",
            message_en="Successfully updated mute status.",
        )
