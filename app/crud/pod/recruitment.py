from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.pod import PodMember
from app.models.user import User
from datetime import datetime, timezone


class RecruitmentCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: 파티 참여 신청
    async def add_member(
        self, pod_id: int, user_id: int, role: str = "member", message: str = None
    ) -> bool:
        # 중복 방지
        q = await self.db.execute(
            select(PodMember).where(
                PodMember.pod_id == pod_id, PodMember.user_id == user_id
            )
        )
        if q.scalar_one_or_none() is not None:
            return True

        # 현재 시간을 Unix timestamp로 저장
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        self.db.add(
            PodMember(
                pod_id=pod_id,
                user_id=user_id,
                role=role,
                message=message,
                created_at=current_timestamp,
            )
        )
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
        q = await self.db.execute(
            select(PodMember)
            .options(selectinload(PodMember.user))
            .where(PodMember.pod_id == pod_id)
        )
        return list(q.scalars().all())
