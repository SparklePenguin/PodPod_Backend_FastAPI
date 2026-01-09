"""Notification Use Case - 알림 비즈니스 로직 처리"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PageDto
from app.features.notifications.schemas import (
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.features.notifications.services.notification_service import NotificationService


class NotificationUseCase:
    """알림 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        notification_service: NotificationService,
    ) -> None:
        """
        Args:
            session: 데이터베이스 세션
            notification_service: 알림 서비스
        """
        self._session = session
        self._notification_service = notification_service

    # MARK: - 알림 목록 조회
    async def get_notifications(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        unread_only: bool = False,
        category: str | None = None,
    ) -> PageDto[NotificationResponse]:
        """사용자의 알림 목록 조회"""
        return await self._notification_service.get_notifications(
            user_id=user_id,
            page=page,
            size=size,
            unread_only=unread_only,
            category=category,
        )

    # MARK: - 읽지 않은 알림 개수 조회
    async def get_unread_count(self, user_id: int) -> NotificationUnreadCountResponse:
        """읽지 않은 알림 개수 조회"""
        return await self._notification_service.get_unread_count(user_id)

    # MARK: - 알림 읽음 처리
    async def mark_as_read(
        self, notification_id: int, user_id: int
    ) -> NotificationResponse:
        """특정 알림을 읽음 처리"""
        try:
            result = await self._notification_service.mark_as_read(
                notification_id, user_id
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 모든 알림 읽음 처리
    async def mark_all_as_read(self, user_id: int) -> dict[str, int]:
        """사용자의 모든 알림을 읽음 처리"""
        try:
            result = await self._notification_service.mark_all_as_read(user_id)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 알림 삭제
    async def delete_notification(
        self, notification_id: int, user_id: int
    ) -> dict[str, bool]:
        """특정 알림 삭제"""
        try:
            result = await self._notification_service.delete_notification(
                notification_id, user_id
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 읽은 알림 전체 삭제
    async def delete_all_read_notifications(self, user_id: int) -> dict[str, int]:
        """읽은 알림 전체 삭제"""
        try:
            result = await self._notification_service.delete_all_read_notifications(
                user_id
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise
