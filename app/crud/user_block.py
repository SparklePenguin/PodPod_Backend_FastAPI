from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, delete, or_
from typing import Optional, List, Tuple
from datetime import datetime
from app.models.user_block import UserBlock
from app.models.user import User


class UserBlockCRUD:
    """사용자 차단 CRUD 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_block(
        self, blocker_id: int, blocked_id: int
    ) -> Optional[UserBlock]:
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
            self.db.add(block)
            await self.db.commit()
            await self.db.refresh(block)
            return block
        except Exception:
            await self.db.rollback()
            return None

    async def delete_block(self, blocker_id: int, blocked_id: int) -> bool:
        """사용자 차단 해제"""
        try:
            block = await self.get_block(blocker_id, blocked_id)
            if not block:
                return False

            await self.db.delete(block)
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False

    async def get_block(self, blocker_id: int, blocked_id: int) -> Optional[UserBlock]:
        """특정 차단 관계 조회"""
        query = select(UserBlock).where(
            and_(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def check_block_exists(self, blocker_id: int, blocked_id: int) -> bool:
        """차단 관계 존재 여부 확인"""
        query = select(UserBlock).where(
            and_(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_blocked_users(
        self, blocker_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Tuple[User, datetime]], int]:
        """차단한 사용자 목록 조회"""
        offset = (page - 1) * size

        # 차단한 사용자 목록 조회
        query = (
            select(User, UserBlock.created_at)
            .join(UserBlock, User.id == UserBlock.blocked_id)
            .where(UserBlock.blocker_id == blocker_id)
            .order_by(desc(UserBlock.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        blocked_data = result.all()

        # 총 차단 수 조회
        count_query = select(func.count(UserBlock.id)).where(
            UserBlock.blocker_id == blocker_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        return blocked_data, total_count

    async def delete_all_by_user(self, user_id: int) -> None:
        """특정 사용자와 관련된 모든 차단 관계 삭제"""
        # 해당 사용자가 차단한 경우와 차단당한 경우 모두 삭제
        await self.db.execute(
            delete(UserBlock).where(
                or_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == user_id)
            )
        )
        await self.db.commit()
