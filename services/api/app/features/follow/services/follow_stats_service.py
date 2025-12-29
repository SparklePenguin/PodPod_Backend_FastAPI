from app.features.follow.repositories.follow_stats_repository import (
    FollowStatsRepository,
)
from app.features.follow.schemas import FollowStatsDto
from sqlalchemy.ext.asyncio import AsyncSession


class FollowStatsService:
    """팔로우 통계 서비스"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._follow_stats_repo = FollowStatsRepository(session)

    # - MARK: 팔로우 통계 조회
    async def get_follow_stats(
        self, user_id: int, current_user_id: int | None = None
    ) -> FollowStatsDto:
        """팔로우 통계 조회"""
        stats = await self._follow_stats_repo.get_follow_stats(user_id, current_user_id)

        return FollowStatsDto(
            following_count=stats["following_count"],
            followers_count=stats["followers_count"],
            is_following=stats["is_following"],
        )
