from app.features.pods.models import PodLike
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class PodLikeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 좋아요 등록
    async def like_pod(self, pod_id: int, user_id: int) -> bool:
        # 중복 좋아요 방지
        exists = await self._session.execute(
            select(PodLike).where(PodLike.pod_id == pod_id, PodLike.user_id == user_id)
        )
        if exists.scalar_one_or_none() is not None:
            return True
        self._session.add(PodLike(pod_id=pod_id, user_id=user_id))
        await self._session.flush()
        return True

    # - MARK: 좋아요 취소
    async def unlike_pod(self, pod_id: int, user_id: int) -> bool:
        q = await self._session.execute(
            select(PodLike).where(PodLike.pod_id == pod_id, PodLike.user_id == user_id)
        )
        row = q.scalar_one_or_none()
        if row is None:
            return True
        await self._session.delete(row)
        await self._session.flush()
        return True

    # - MARK: 좋아요 개수
    async def like_count(self, pod_id: int) -> int:
        q = await self._session.execute(
            select(func.count(PodLike.id)).where(PodLike.pod_id == pod_id)
        )
        return int(q.scalar() or 0)

    # - MARK: 좋아요 상태
    async def is_liked(self, pod_id: int, user_id: int) -> bool:
        q = await self._session.execute(
            select(PodLike.id).where(
                PodLike.pod_id == pod_id, PodLike.user_id == user_id
            )
        )
        return q.scalar_one_or_none() is not None

    # - MARK: 좋아요한 사용자 목록 조회
    async def get_users_who_liked_pod(self, pod_id: int):
        """파티를 좋아요한 사용자 목록 조회"""
        from app.features.users.models import User

        query = (
            select(User)
            .join(PodLike, User.id == PodLike.user_id)
            .where(PodLike.pod_id == pod_id)
            .distinct()
        )
        result = await self._session.execute(query)
        return result.scalars().all()

    # - MARK: 사용자 관련 삭제 메서드
    async def delete_all_likes_by_user_id(self, user_id: int) -> None:
        """사용자의 모든 파티 좋아요 삭제"""
        from sqlalchemy import delete

        await self._session.execute(
            delete(PodLike).where(PodLike.user_id == user_id)
        )
