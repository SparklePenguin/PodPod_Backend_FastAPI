from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.features.pods.models.pod import PodLike


class PodLikeCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: 좋아요 등록
    async def like_pod(self, pod_id: int, user_id: int) -> bool:
        # 중복 좋아요 방지
        exists = await self.db.execute(
            select(PodLike).where(PodLike.pod_id == pod_id, PodLike.user_id == user_id)
        )
        if exists.scalar_one_or_none() is not None:
            return True
        self.db.add(PodLike(pod_id=pod_id, user_id=user_id))
        await self.db.commit()
        return True

    # - MARK: 좋아요 취소
    async def unlike_pod(self, pod_id: int, user_id: int) -> bool:
        q = await self.db.execute(
            select(PodLike).where(PodLike.pod_id == pod_id, PodLike.user_id == user_id)
        )
        row = q.scalar_one_or_none()
        if row is None:
            return True
        await self.db.delete(row)
        await self.db.commit()
        return True

    # - MARK: 좋아요 개수
    async def like_count(self, pod_id: int) -> int:
        q = await self.db.execute(
            select(func.count(PodLike.id)).where(PodLike.pod_id == pod_id)
        )
        return int(q.scalar() or 0)

    # - MARK: 좋아요 상태
    async def is_liked(self, pod_id: int, user_id: int) -> bool:
        q = await self.db.execute(
            select(PodLike.id).where(
                PodLike.pod_id == pod_id, PodLike.user_id == user_id
            )
        )
        return q.scalar_one_or_none() is not None
