from typing import List, Tuple

from app.features.follow.models import Follow
from app.features.pods.models.pod import Pod
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class FollowPodRepository:
    """팔로우한 사용자의 파티 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 팔로우하는 사용자가 만든 파티 목록 조회
    async def get_following_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Pod], int]:
        """팔로우하는 사용자가 만든 파티 목록 조회"""
        from app.features.pods.models.pod.pod_status import PodStatus

        offset = (page - 1) * size

        # 팔로우하는 사용자들이 만든 파티 조회 (활성화된 팔로우만, 모집중인 파티만)
        query = (
            select(Pod)
            .options(selectinload(Pod.images))
            .join(Follow, Pod.owner_id == Follow.following_id)
            .where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.is_active,  # 활성화된 팔로우만
                    Pod.is_active,  # 활성화된 파티만
                    Pod.status == PodStatus.RECRUITING,  # 모집중인 파티만
                )
            )
            .order_by(desc(Pod.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self._session.execute(query)
        pods = result.scalars().all()

        # 총 파티 수 조회 (활성화된 팔로우만, 모집중인 파티만)
        count_query = (
            select(func.count(Pod.id))
            .join(Follow, Pod.owner_id == Follow.following_id)
            .where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.is_active,  # 활성화된 팔로우만
                    Pod.is_active,  # 활성화된 파티만
                    Pod.status == PodStatus.RECRUITING,  # 모집중인 파티만
                )
            )
        )
        count_result = await self._session.execute(count_query)
        total_count = count_result.scalar() or 0

        return list(pods), total_count
