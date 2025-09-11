from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.pod import PodMember


class RecruitmentCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: 파티 참여 신청
    async def add_member(self, pod_id: int, user_id: int, role: str = "member") -> bool:
        # 중복 방지
        q = await self.db.execute(
            select(PodMember).where(
                PodMember.pod_id == pod_id, PodMember.user_id == user_id
            )
        )
        if q.scalar_one_or_none() is not None:
            return True
        self.db.add(PodMember(pod_id=pod_id, user_id=user_id, role=role))
        await self.db.commit()
        return True

    async def remove_member(self, pod_id: int, user_id: int) -> bool:
        q = await self.db.execute(
            select(PodMember).where(
                PodMember.pod_id == pod_id, PodMember.user_id == user_id
            )
        )
        row = q.scalar_one_or_none()
        if row is None:
            return True
        await self.db.delete(row)
        await self.db.commit()
        return True

    async def list_members(self, pod_id: int) -> list[PodMember]:
        q = await self.db.execute(select(PodMember).where(PodMember.pod_id == pod_id))
        return list(q.scalars().all())
