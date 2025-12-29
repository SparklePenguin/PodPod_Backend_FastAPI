from datetime import datetime
from typing import List, Tuple

from app.features.users.models import User, UserBlock
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class BlockUserRepository:
    """사용자 차단 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 차단 생성
    async def create_block(self, blocker_id: int, blocked_id: int) -> UserBlock | None:
        """사용자 차단 생성"""
        try:
            # 자기 자신을 차단하는지 확인
            if blocker_id == blocked_id:
                return None

            # 이미 차단하고 있는지 확인
            existing_block = await self.get_block(blocker_id, blocked_id)
            if existing_block:
                return existing_block

            block = UserBlock(blocker_id=blocker_id, blocked_id=blocked_id)
            self._session.add(block)
            await self._session.commit()
            await self._session.refresh(block)
            return block
        except Exception:
            await self._session.rollback()
            return None

    # - MARK: 차단 해제
    async def delete_block(self, blocker_id: int, blocked_id: int) -> bool:
        """사용자 차단 해제"""
        try:
            block = await self.get_block(blocker_id, blocked_id)
            if not block:
                return False

            await self._session.delete(block)
            await self._session.commit()
            return True
        except Exception:
            await self._session.rollback()
            return False

    # - MARK: 차단 관계 조회
    async def get_block(self, blocker_id: int, blocked_id: int) -> UserBlock | None:
        """특정 차단 관계 조회"""
        query = select(UserBlock).where(
            and_(UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    # - MARK: 차단한 사용자 목록 조회
    async def get_blocked_users(
        self, blocker_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Tuple[User, datetime]], int]:
        """차단한 사용자 목록 조회 (페이징 지원)"""
        offset = (page - 1) * size

        # 차단한 사용자 목록 조회 (JOIN으로 N+1 문제 방지)
        query = (
            select(User, UserBlock.created_at)
            .join(UserBlock, User.id == UserBlock.blocked_id)
            .where(UserBlock.blocker_id == blocker_id)
            .order_by(desc(UserBlock.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self._session.execute(query)
        blocked_data_raw = result.all()

        # Row 객체를 Tuple로 변환
        blocked_data: List[Tuple[User, datetime]] = [
            (row[0], row[1]) for row in blocked_data_raw
        ]

        # 총 차단 수 조회
        count_query = select(func.count(UserBlock.id)).where(
            UserBlock.blocker_id == blocker_id
        )
        count_result = await self._session.execute(count_query)
        total_count = count_result.scalar() or 0

        return blocked_data, total_count
