from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.pod.pod_like import PodLikeCRUD


class PodLikeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = PodLikeCRUD(db)

    # - MARK: 좋아요 등록
    async def like_pod(self, pod_id: int, user_id: int) -> dict:
        ok = await self.crud.like_pod(pod_id, user_id)
        return {"liked": ok}

    # - MARK: 좋아요 취소
    async def unlike_pod(self, pod_id: int, user_id: int) -> dict:
        ok = await self.crud.unlike_pod(pod_id, user_id)
        return {"unliked": ok}

    # - MARK: 좋아요 상태
    async def like_status(self, pod_id: int, user_id: int) -> dict:
        return {
            "liked": await self.crud.is_liked(pod_id, user_id),
            "count": await self.crud.like_count(pod_id),
        }
