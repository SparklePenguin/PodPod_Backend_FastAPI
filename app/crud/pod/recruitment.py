from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.pod import PodMember, Pod
from app.models.pod.pod_status import PodStatus
from app.models.user import User
from datetime import datetime, timezone


class RecruitmentCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: 파티 참여 신청
    async def add_member(
        self, pod_id: int, user_id: int, role: str = "member", message: str = None
    ) -> PodMember:
        # 중복 방지
        q = await self.db.execute(
            select(PodMember).where(
                PodMember.pod_id == pod_id, PodMember.user_id == user_id
            )
        )
        existing_member = q.scalar_one_or_none()
        if existing_member is not None:
            return existing_member

        # 파티 정보 조회 및 capacity 체크
        pod_q = await self.db.execute(select(Pod).where(Pod.id == pod_id))
        pod = pod_q.scalar_one_or_none()
        if not pod:
            raise ValueError("파티를 찾을 수 없습니다")

        # 현재 멤버 수 확인
        member_count_q = await self.db.execute(
            select(func.count(PodMember.id)).where(PodMember.pod_id == pod_id)
        )
        current_member_count = member_count_q.scalar() or 0

        # capacity 체크 (owner는 이미 포함되어 있으므로 role이 member인 경우만 체크)
        if role == "member" and current_member_count >= pod.capacity:
            raise ValueError("파티 정원이 가득 찼습니다")

        # 현재 시간을 Unix timestamp로 저장
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        pod_member = PodMember(
            pod_id=pod_id,
            user_id=user_id,
            role=role,
            message=message,
            joined_at=current_timestamp,
        )
        self.db.add(pod_member)

        # 멤버 추가 후 정원이 가득 찼는지 확인하고 상태 업데이트
        if role == "member":
            # 새 멤버 추가 후의 총 멤버 수
            new_member_count = current_member_count + 1
            if new_member_count >= pod.capacity and pod.status == PodStatus.RECRUITING:
                pod.status = PodStatus.COMPLETED

        await self.db.commit()
        await self.db.refresh(pod_member)
        return pod_member

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
