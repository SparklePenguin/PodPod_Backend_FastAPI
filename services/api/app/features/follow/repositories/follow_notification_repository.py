from app.features.follow.repositories.follow_repository import FollowRepository
from sqlalchemy.ext.asyncio import AsyncSession


class FollowNotificationRepository:
    """팔로우 알림 설정 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._follow_repo = FollowRepository(session)

    # - MARK: 알림 설정 상태 조회
    async def get_notification_status(
        self, follower_id: int, following_id: int
    ) -> bool | None:
        """특정 팔로우 관계의 알림 설정 상태 조회"""
        follow = await self._follow_repo.get_follow(follower_id, following_id)
        if not follow:
            return None
        return bool(getattr(follow, "notification_enabled", False))

    # - MARK: 알림 설정 상태 변경
    async def update_notification_status(
        self, follower_id: int, following_id: int, notification_enabled: bool
    ) -> bool:
        """특정 팔로우 관계의 알림 설정 상태 변경"""
        try:
            follow = await self._follow_repo.get_follow(follower_id, following_id)
            if not follow:
                return False

            setattr(follow, "notification_enabled", notification_enabled)
            await self._session.commit()
            await self._session.refresh(follow)
            return True
        except Exception:
            await self._session.rollback()
            return False
