from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.pod import PodCRUD
from app.core.error_codes import raise_error


class RecruitmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = PodCRUD(db)

    # - MARK: 파티 참여 신청
    async def apply_to_pod(self, pod_id: int, user_id: int) -> dict:
        pod = await self.crud.get_pod_by_id(pod_id)
        if pod is None:
            raise_error("POD_NOT_FOUND")
        already = any(m.user_id == user_id for m in pod.members)
        if already:
            return {"applied": True, "alreadyMember": True}
        await self.crud.add_member(pod_id, user_id, role="member")
        return {"applied": True, "alreadyMember": False}
