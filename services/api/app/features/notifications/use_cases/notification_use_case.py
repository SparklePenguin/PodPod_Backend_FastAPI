"""Notification Use Case - 알림 비즈니스 로직 처리"""

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PageDto
from app.features.notifications.exceptions import NotificationNotFoundException
from app.features.notifications.repositories.notification_repository import (
    NotificationRepository,
)
from app.features.notifications.schemas import (
    NotificationDto,
    NotificationUnreadCountResponse,
)
from app.features.notifications.services.notification_dto_service import (
    NotificationDtoService,
)

if TYPE_CHECKING:
    from app.features.tendencies.repositories.tendency_repository import (
        TendencyRepository,
    )


class NotificationUseCase:
    """알림 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        notification_repo: NotificationRepository,
        tendency_repo: "TendencyRepository",
        dto_service: NotificationDtoService,
    ) -> None:
        """
        Args:
            session: 데이터베이스 세션
            notification_repo: 알림 레포지토리
            tendency_repo: 성향 레포지토리
            dto_service: 알림 DTO 변환 서비스
        """
        self._session = session
        self._notification_repo = notification_repo
        self._tendency_repo = tendency_repo
        self._dto_service = dto_service

    # MARK: - 알림 목록 조회
    async def get_notifications(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        unread_only: bool = False,
        category: str | None = None,
    ) -> PageDto[NotificationDto]:
        """사용자의 알림 목록 조회"""
        skip = (page - 1) * size

        # category를 대문자로 변환 (DB에는 대문자로 저장됨)
        category_upper = category.upper() if category else None

        # 알림 목록 조회
        notifications = await self._notification_repo.get_user_notifications(
            user_id=user_id,
            skip=skip,
            limit=size,
            unread_only=unread_only,
            category=category_upper,
        )

        # 전체 개수 조회
        total_count = await self._notification_repo.get_total_count(
            user_id=user_id, unread_only=unread_only, category=category_upper
        )

        # DTO 변환
        notification_dtos: list[NotificationDto] = []
        for n in notifications:
            notification_dto = await self._dto_service.convert_to_notification_response(
                n
            )
            notification_dtos.append(notification_dto)

        return PageDto.create(
            items=notification_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # MARK: - 읽지 않은 알림 개수 조회
    async def get_unread_count(self, user_id: int) -> NotificationUnreadCountResponse:
        """읽지 않은 알림 개수 조회"""
        unread_count = await self._notification_repo.get_unread_count(user_id)
        return NotificationUnreadCountResponse(unread_count=unread_count)

    # MARK: - 알림 읽음 처리
    async def mark_as_read(
        self, notification_id: int, user_id: int
    ) -> NotificationDto:
        """특정 알림을 읽음 처리"""
        try:
            notification = await self._notification_repo.mark_as_read(
                notification_id, user_id
            )

            if not notification:
                raise NotificationNotFoundException(notification_id)

            result = await self._dto_service.convert_to_notification_response(
                notification
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
            updated_count = await self._notification_repo.mark_all_as_read(user_id)
            await self._session.commit()
            return {"updatedCount": updated_count}
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 알림 삭제
    async def delete_notification(
        self, notification_id: int, user_id: int
    ) -> dict[str, bool]:
        """특정 알림 삭제"""
        try:
            success = await self._notification_repo.delete_notification(
                notification_id, user_id
            )

            if not success:
                raise NotificationNotFoundException(notification_id)

            await self._session.commit()
            return {"success": True}
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 읽은 알림 전체 삭제
    async def delete_all_read_notifications(self, user_id: int) -> dict[str, int]:
        """읽은 알림 전체 삭제"""
        try:
            deleted_count = await self._notification_repo.delete_all_read_notifications(
                user_id
            )
            await self._session.commit()
            return {"deletedCount": deleted_count}
        except Exception:
            await self._session.rollback()
            raise
