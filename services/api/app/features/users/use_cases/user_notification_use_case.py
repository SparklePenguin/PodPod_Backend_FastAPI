"""User Notification Use Case - 사용자 알림 설정 관련 비즈니스 로직 처리"""

from app.features.notifications.services.notification_dto_service import (
    NotificationDtoService,
)
from app.features.users.repositories import UserNotificationRepository
from app.features.users.schemas import (
    UpdateUserNotificationSettingsRequest,
    UserNotificationSettingsDto,
)
from sqlalchemy.ext.asyncio import AsyncSession


class UserNotificationUseCase:
    """사용자 알림 설정 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        notification_repo: UserNotificationRepository,
        notification_dto_service: NotificationDtoService,
    ):
        self._session = session
        self._notification_repo = notification_repo
        self._notification_dto_service = notification_dto_service

    # - MARK: 알림 설정 조회
    async def get_notification_settings(
        self, user_id: int
    ) -> UserNotificationSettingsDto:
        """사용자 알림 설정 조회"""
        settings = await self._notification_repo.get_by_user_id(user_id)

        if not settings:
            # 설정이 없으면 기본 설정 생성
            settings = await self._notification_repo.create_default_settings(user_id)
            await self._session.commit()
            await self._session.refresh(settings)

        # DTO 변환은 notification_dto_service에서 처리
        return self._notification_dto_service.convert_notification_settings_to_dto(
            settings
        )

    # - MARK: 알림 설정 업데이트
    async def update_notification_settings(
        self, user_id: int, update_data: UpdateUserNotificationSettingsRequest
    ) -> UserNotificationSettingsDto:
        """사용자 알림 설정 업데이트"""
        # 기존 설정 확인
        settings = await self._notification_repo.get_by_user_id(user_id)
        if not settings:
            # 설정이 없으면 기본 설정 생성
            settings = await self._notification_repo.create_default_settings(user_id)
            await self._session.commit()
            await self._session.refresh(settings)

        # 설정 업데이트
        updated_settings = await self._notification_repo.update_settings(
            user_id, update_data
        )
        if not updated_settings:
            from app.features.users.exceptions import UserNotFoundException

            raise UserNotFoundException(user_id)

        # 트랜잭션 커밋
        await self._session.commit()
        await self._session.refresh(updated_settings)

        # DTO 변환은 notification_dto_service에서 처리
        return self._notification_dto_service.convert_notification_settings_to_dto(
            updated_settings
        )
