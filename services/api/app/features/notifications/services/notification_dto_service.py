"""Notification DTO Service - 알림 설정 DTO 변환 로직"""

from app.features.users.models import UserNotificationSettings
from app.features.users.schemas import UserNotificationSettingsDto


class NotificationDtoService:
    """알림 설정 DTO 변환 서비스"""

    @staticmethod
    def convert_notification_settings_to_dto(
        settings: UserNotificationSettings,
    ) -> UserNotificationSettingsDto:
        """알림 설정 모델을 DTO로 변환"""
        do_not_disturb_start_value = settings.do_not_disturb_start
        do_not_disturb_end_value = settings.do_not_disturb_end

        return UserNotificationSettingsDto(
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
