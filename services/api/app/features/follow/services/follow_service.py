from app.common.schemas import PageDto
from app.core.services.fcm_service import FCMService
from app.features.follow.exceptions import (
    FollowFailedException,
    FollowInvalidException,
)
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.follow.schemas import (
    FollowInfoDto,
    FollowNotificationStatusDto,
    FollowStatsDto,
)
from app.features.follow.services.follow_list_service import FollowListService
from app.features.follow.services.follow_notification_service import (
    FollowNotificationService,
)
from app.features.follow.services.follow_pod_service import FollowPodService
from app.features.follow.services.follow_stats_service import FollowStatsService
from app.features.pods.schemas import PodDetailDto
from app.features.users.schemas import UserDto
from sqlalchemy.ext.asyncio import AsyncSession


class FollowService:
    """팔로우 서비스 - 모든 팔로우 관련 기능 통합"""

    def __init__(self, session: AsyncSession, fcm_service: FCMService | None = None):
        self._session = session
        self._follow_repo = FollowRepository(session)
        self._follow_list_service = FollowListService(session)
        self._follow_stats_service = FollowStatsService(session)
        self._follow_notification_service = FollowNotificationService(
            session, fcm_service
        )
        self._follow_pod_service = FollowPodService(session)

    # - MARK: 사용자 팔로우
    async def follow_user(self, follower_id: int, following_id: int) -> FollowInfoDto:
        """사용자 팔로우"""
        follow = await self._follow_repo.create_follow(follower_id, following_id)

        if not follow:
            raise FollowFailedException(follower_id, following_id)

        if follow.follower_id is None or follow.following_id is None:
            raise FollowInvalidException("팔로우 정보가 올바르지 않습니다.")

        created_at_value = follow.created_at
        if created_at_value is None:
            from datetime import datetime, timezone

            created_at_value = datetime.now(timezone.utc)

        follow_info = FollowInfoDto(
            follower_id=follow.follower_id,
            following_id=follow.following_id,
            created_at=created_at_value,
        )

        # 팔로우 알림 전송
        await self._follow_notification_service.send_follow_notification(
            follower_id, following_id
        )

        return follow_info

    # - MARK: 사용자 팔로우 취소
    async def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        """사용자 팔로우 취소"""
        success = await self._follow_repo.delete_follow(follower_id, following_id)
        if not success:
            from app.features.follow.exceptions import FollowNotFoundException

            raise FollowNotFoundException(follower_id, following_id)
        return success

    # - MARK: 팔로우하는 사용자 목록 조회
    async def get_following_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserDto]:
        """팔로우하는 사용자 목록 조회"""
        return await self._follow_list_service.get_following_list(user_id, page, size)

    # - MARK: 팔로워 목록 조회
    async def get_followers_list(
        self,
        user_id: int,
        current_user_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[UserDto]:
        """팔로워 목록 조회"""
        return await self._follow_list_service.get_followers_list(
            user_id, current_user_id, page, size
        )

    # - MARK: 팔로우 통계 조회
    async def get_follow_stats(
        self, user_id: int, current_user_id: int | None = None
    ) -> FollowStatsDto:
        """팔로우 통계 조회"""
        return await self._follow_stats_service.get_follow_stats(
            user_id, current_user_id
        )

    # - MARK: 팔로우하는 사용자가 만든 파티 목록 조회
    async def get_following_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDetailDto]:
        """팔로우하는 사용자가 만든 파티 목록 조회"""
        return await self._follow_pod_service.get_following_pods(user_id, page, size)

    # - MARK: 추천 유저 목록 조회
    async def get_recommended_users(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserDto]:
        """추천 유저 목록 조회"""
        return await self._follow_list_service.get_recommended_users(
            user_id, page, size
        )

    # - MARK: 특정 팔로우 관계의 알림 설정 상태 조회
    async def get_notification_status(
        self, follower_id: int, following_id: int
    ) -> FollowNotificationStatusDto | None:
        """특정 팔로우 관계의 알림 설정 상태 조회"""
        return await self._follow_notification_service.get_notification_status(
            follower_id, following_id
        )

    # - MARK: 특정 팔로우 관계의 알림 설정 상태 변경
    async def update_notification_status(
        self, follower_id: int, following_id: int, notification_enabled: bool
    ) -> FollowNotificationStatusDto | None:
        """특정 팔로우 관계의 알림 설정 상태 변경"""
        return await self._follow_notification_service.update_notification_status(
            follower_id, following_id, notification_enabled
        )

    # - MARK: 팔로우한 유저의 파티 생성 알림
    async def send_followed_user_pod_created_notification(
        self, pod_owner_id: int, pod_id: int
    ) -> None:
        """팔로우한 유저가 파티 생성 시 팔로워들에게 알림 전송"""
        await self._follow_notification_service.send_followed_user_pod_created_notification(
            pod_owner_id, pod_id
        )
