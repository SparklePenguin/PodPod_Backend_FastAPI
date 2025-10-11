"""
알림 CRUD
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from typing import Optional, List
from datetime import datetime, timezone

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate


class NotificationCRUD:
    """알림 CRUD 클래스"""

    async def create(
        self, db: AsyncSession, notification_in: NotificationCreate
    ) -> Notification:
        """알림 생성"""
        notification = Notification(
            user_id=notification_in.user_id,
            title=notification_in.title,
            body=notification_in.body,
            notification_type=notification_in.notification_type,
            notification_value=notification_in.notification_value,
            related_id=notification_in.related_id,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def get_by_id(
        self, db: AsyncSession, notification_id: int
    ) -> Optional[Notification]:
        """ID로 알림 조회"""
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> List[Notification]:
        """
        사용자의 알림 목록 조회

        Args:
            db: DB 세션
            user_id: 사용자 ID
            skip: 페이지네이션 offset
            limit: 페이지네이션 limit
            unread_only: 읽지 않은 알림만 조회할지 여부
        """
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)

        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_total_count(
        self, db: AsyncSession, user_id: int, unread_only: bool = False
    ) -> int:
        """
        사용자의 전체 알림 개수 조회

        Args:
            db: DB 세션
            user_id: 사용자 ID
            unread_only: 읽지 않은 알림만 카운트할지 여부
        """
        query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.where(Notification.is_read == False)

        result = await db.execute(query)
        return result.scalar_one()

    async def get_unread_count(self, db: AsyncSession, user_id: int) -> int:
        """읽지 않은 알림 개수 조회"""
        return await self.get_total_count(db, user_id, unread_only=True)

    async def mark_as_read(
        self, db: AsyncSession, notification_id: int, user_id: int
    ) -> Optional[Notification]:
        """
        알림을 읽음 처리

        Args:
            db: DB 세션
            notification_id: 알림 ID
            user_id: 사용자 ID (권한 확인용)
        """
        notification = await self.get_by_id(db, notification_id)

        if not notification or notification.user_id != user_id:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(notification)

        return notification

    async def mark_all_as_read(self, db: AsyncSession, user_id: int) -> int:
        """
        사용자의 모든 알림을 읽음 처리

        Returns:
            읽음 처리된 알림 개수
        """
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def delete_notification(
        self, db: AsyncSession, notification_id: int, user_id: int
    ) -> bool:
        """
        알림 삭제

        Args:
            db: DB 세션
            notification_id: 알림 ID
            user_id: 사용자 ID (권한 확인용)

        Returns:
            삭제 성공 여부
        """
        notification = await self.get_by_id(db, notification_id)

        if not notification or notification.user_id != user_id:
            return False

        await db.delete(notification)
        await db.commit()
        return True

    async def delete_all_read_notifications(
        self, db: AsyncSession, user_id: int
    ) -> int:
        """
        읽은 알림 전체 삭제

        Returns:
            삭제된 알림 개수
        """
        stmt = delete(Notification).where(
            Notification.user_id == user_id, Notification.is_read == True
        )

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount


# 싱글톤 인스턴스
notification_crud = NotificationCRUD()
