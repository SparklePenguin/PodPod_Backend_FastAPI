from app.features.users.repositories import UserNotificationRepository
from app.features.users.schemas import (
    UpdateUserNotificationSettingsRequest,
    UserNotificationSettingsDto,
)
from sqlalchemy.ext.asyncio import AsyncSession


class UserNotificationService:
    """사용자 알림 설정 서비스"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._notification_repo = UserNotificationRepository(session)

    # - MARK: 알림 설정 조회
    async def get_notification_settings(
        self, user_id: int
    ) -> UserNotificationSettingsDto:
        """사용자 알림 설정 조회"""
        settings = await self._notification_repo.get_by_user_id(user_id)

        if not settings:
            # 설정이 없으면 기본 설정 생성
            settings = await self._notification_repo.create_default_settings(user_id)

        # DTO 변환
        do_not_disturb_start_value = settings.do_not_disturb_start
        do_not_disturb_end_value = settings.do_not_disturb_end

        settings_dto = UserNotificationSettingsDto(
            id=settings.id,
            user_id=settings.user_id,
            wake_up_alarm=bool(settings.notice_enabled),
            bus_alert=bool(settings.chat_enabled),
            party_alert=bool(settings.pod_enabled),
            community_alert=bool(settings.community_enabled),
            product_alarm=bool(settings.marketing_enabled),
            do_not_disturb_enabled=bool(settings.do_not_disturb_enabled),
            start_time=(
                int(
                    do_not_disturb_start_value.hour * 3600
                    + do_not_disturb_start_value.minute * 60
                )
                * 1000
                if do_not_disturb_start_value is not None
                else None
            ),
            end_time=(
                int(
                    do_not_disturb_end_value.hour * 3600
                    + do_not_disturb_end_value.minute * 60
                )
                * 1000
                if do_not_disturb_end_value is not None
                else None
            ),
            marketing_enabled=bool(settings.marketing_enabled),
        )

        return settings_dto

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

        # 설정 업데이트
        updated_settings = await self._notification_repo.update_settings(
            user_id, update_data
        )
        if not updated_settings:
            from app.features.users.exceptions import UserNotFoundException

            raise UserNotFoundException(user_id)

        # DTO 변환
        do_not_disturb_start_value = updated_settings.do_not_disturb_start
        do_not_disturb_end_value = updated_settings.do_not_disturb_end

        settings_dto = UserNotificationSettingsDto(
            id=updated_settings.id,
            user_id=updated_settings.user_id,
            wake_up_alarm=bool(updated_settings.notice_enabled),
            bus_alert=bool(updated_settings.chat_enabled),
            party_alert=bool(updated_settings.pod_enabled),
            community_alert=bool(updated_settings.community_enabled),
            product_alarm=bool(updated_settings.marketing_enabled),
            do_not_disturb_enabled=bool(updated_settings.do_not_disturb_enabled),
            start_time=(
                int(
                    do_not_disturb_start_value.hour * 3600
                    + do_not_disturb_start_value.minute * 60
                )
                * 1000
                if do_not_disturb_start_value is not None
                else None
            ),
            end_time=(
                int(
                    do_not_disturb_end_value.hour * 3600
                    + do_not_disturb_end_value.minute * 60
                )
                * 1000
                if do_not_disturb_end_value is not None
                else None
            ),
            marketing_enabled=bool(updated_settings.marketing_enabled),
        )

        return settings_dto

    # - MARK: 알림 전송 여부 확인
    async def should_send_notification(
        self, user_id: int, notification_category: str
    ) -> bool:
        """알림 전송 여부 확인"""
        return await self._notification_repo.should_send_notification(
            user_id, notification_category
        )
