from app.features.follow.models import Follow
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class FollowStatsRepository:
    """팔로우 통계 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 팔로우 통계 조회
    async def get_follow_stats(
        self, user_id: int, current_user_id: int | None = None
    ) -> dict:
        """팔로우 통계 조회 (자기 자신 제외)"""
        # 팔로우하는 수 (자기 자신 제외, 활성화된 것만)
        following_count_query = select(func.count(Follow.id)).where(
            and_(
                Follow.follower_id == user_id,
                Follow.following_id != user_id,  # 자기 자신 제외
                Follow.is_active,  # 활성화된 팔로우만
            )
        )
        following_count_result = await self._session.execute(following_count_query)
        following_count = following_count_result.scalar()

        # 팔로워 수 (자기 자신 제외, 활성화된 것만)
        followers_count_query = select(func.count(Follow.id)).where(
            and_(
                Follow.following_id == user_id,
                Follow.follower_id != user_id,  # 자기 자신 제외
                Follow.is_active,  # 활성화된 팔로우만
            )
        )
        followers_count_result = await self._session.execute(followers_count_query)
        followers_count = followers_count_result.scalar()

        # 현재 사용자가 해당 사용자를 팔로우하는지 확인
        is_following = False
        if current_user_id and current_user_id != user_id:
            from app.features.follow.repositories.follow_repository import (
                FollowRepository,
            )

            follow_repo = FollowRepository(self._session)
            follow = await follow_repo.get_follow(current_user_id, user_id)
            is_following = follow is not None

        return {
            "following_count": following_count,
            "followers_count": followers_count,
            "is_following": is_following,
        }
