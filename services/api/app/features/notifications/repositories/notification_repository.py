from datetime import datetime, timezone
from typing import List

from app.features.notifications.models.notification_models import Notification
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class NotificationRepository:
    """알림 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 알림 생성
    async def create_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str,
        notification_value: str,
        related_user_id: int | None = None,
        related_pod_id: int | None = None,
        related_id: str | None = None,
        category: str = "pod",
    ) -> Notification:
        """알림 생성"""
        notification = Notification(
            user_id=user_id,
            related_user_id=related_user_id,
            related_pod_id=related_pod_id,
            title=title,
            body=body,
            notification_type=notification_type,
            notification_value=notification_value,
            related_id=related_id,
            category=category,
        )
        self._session.add(notification)
        await self._session.commit()
        await self._session.refresh(notification)
        return notification

    # - MARK: ID로 알림 조회
    async def get_by_id(self, notification_id: int) -> Notification | None:
        """ID로 알림 조회"""
        result = await self._session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    # - MARK: 사용자 알림 목록 조회
    async def get_user_notifications(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        category: str | None = None,
    ) -> List[Notification]:
        """사용자의 알림 목록 조회"""
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read.is_(False))

        if category:
            query = query.where(Notification.category == category)

        # related_user, related_pod 정보를 함께 로드
        query = query.options(
            selectinload(Notification.related_user),
            selectinload(Notification.related_pod),
        )
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    # - MARK: 전체 알림 개수 조회
    async def get_total_count(
        self,
        user_id: int,
        unread_only: bool = False,
        category: str | None = None,
    ) -> int:
        """사용자의 전체 알림 개수 조회"""
        query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.where(Notification.is_read.is_(False))

        if category:
            query = query.where(Notification.category == category)

        result = await self._session.execute(query)
        return result.scalar_one()

    # - MARK: 읽지 않은 알림 개수 조회
    async def get_unread_count(self, user_id: int) -> int:
        """읽지 않은 알림 개수 조회"""
        return await self.get_total_count(user_id, unread_only=True)

    # - MARK: 알림 읽음 처리
    async def mark_as_read(
        self, notification_id: int, user_id: int
    ) -> Notification | None:
        """알림을 읽음 처리"""
        # 관계를 미리 로드하여 lazy loading 에러 방지
        query = select(Notification).where(Notification.id == notification_id)
        query = query.options(
            selectinload(Notification.related_user),
            selectinload(Notification.related_pod),
        )
        result = await self._session.execute(query)
        notification = result.scalar_one_or_none()

        if not notification or notification.user_id != user_id:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await self._session.commit()
            # refresh는 관계를 무효화할 수 있으므로, 관계를 다시 로드하기 위해 다시 쿼리
            query = select(Notification).where(Notification.id == notification_id)
            query = query.options(
                selectinload(Notification.related_user),
                selectinload(Notification.related_pod),
            )
            result = await self._session.execute(query)
            notification = result.scalar_one()

        return notification

    # - MARK: 모든 알림 읽음 처리
    async def mark_all_as_read(self, user_id: int) -> int:
        """사용자의 모든 알림을 읽음 처리"""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(
                is_read=True, read_at=datetime.now(timezone.utc)
            )
        )

        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount

    # - MARK: 알림 삭제
    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """알림 삭제"""
        notification = await self.get_by_id(notification_id)

        if not notification or notification.user_id != user_id:
            return False

        await self._session.delete(notification)
        await self._session.commit()
        return True

    # - MARK: 읽은 알림 전체 삭제
    async def delete_all_read_notifications(self, user_id: int) -> int:
        """읽은 알림 전체 삭제"""
        stmt = delete(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(True)
        )

        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount

    # - MARK: 사용자 관련 알림 삭제
    async def delete_all_by_user_id(self, user_id: int) -> None:
        """사용자 ID와 관련된 모든 알림 삭제 (user_id와 related_user_id 모두)"""
        await self._session.execute(
            delete(Notification).where(
                (Notification.user_id == user_id)
                | (Notification.related_user_id == user_id)
            )
        )
