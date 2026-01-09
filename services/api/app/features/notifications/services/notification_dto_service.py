"""Notification DTO Service - 알림 DTO 변환 로직"""

from datetime import time
from typing import TYPE_CHECKING

from app.features.notifications.models import Notification
from app.features.notifications.schemas import (
    NotificationDto,
    get_notification_main_type,
)
from app.features.pods.services.pod_dto_service import PodDtoService
from app.features.users.models import User, UserNotificationSettings
from app.features.users.schemas import UserDto, UserNotificationSettingsDto

if TYPE_CHECKING:
    from app.features.tendencies.repositories.tendency_repository import (
        TendencyRepository,
    )


class NotificationDtoService:
    """알림 DTO 변환 서비스 (Stateless)"""

    def __init__(
        self,
        tendency_repo: "TendencyRepository | None" = None,
    ) -> None:
        """
        Args:
            tendency_repo: 성향 레포지토리 (알림 변환 시 필요, 선택적)
        """
        self._tendency_repo = tendency_repo

    @staticmethod
    def convert_notification_settings_to_dto(
        settings: UserNotificationSettings,
    ) -> UserNotificationSettingsDto:
        """알림 설정 모델을 DTO로 변환"""
        do_not_disturb_start_value: time | None = settings.do_not_disturb_start
        do_not_disturb_end_value: time | None = settings.do_not_disturb_end

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

    async def convert_to_notification_response(
        self, notification: Notification
    ) -> NotificationDto:
        """알림 모델을 NotificationResponse DTO로 변환"""
        # related_user DTO 생성
        related_user_dto = await self._create_related_user_dto(notification)

        # related_pod DTO 생성
        related_pod_dto = self._create_related_pod_dto(notification)

        # related_id를 int로 변환
        related_id_int = self._parse_related_id(notification.related_id)

        return NotificationDto(
            id=notification.id,
            title=notification.title,
            body=notification.body,
            type=get_notification_main_type(notification.notification_type),
            value=notification.notification_value,
            related_id=related_id_int,
            category=notification.category,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
            related_user=related_user_dto,
            related_pod=related_pod_dto,
        )

    async def _create_related_user_dto(
        self, notification: Notification
    ) -> UserDto | None:
        """알림의 관련 사용자 DTO 생성"""
        related_user: User | None = notification.related_user
        if not related_user:
            return None

        # 사용자의 성향 정보 조회
        tendency_type = ""
        if self._tendency_repo:
            try:
                user_tendency = await self._tendency_repo.get_user_tendency_result(
                    related_user.id
                )
                if user_tendency:
                    tendency_type_raw = user_tendency.tendency_type
                    tendency_type = (
                        str(tendency_type_raw) if tendency_type_raw is not None else ""
                    )
            except Exception:
                tendency_type = ""

        return UserDto(
            id=related_user.id,
            nickname=related_user.nickname,
            profile_image=related_user.profile_image,
            intro=related_user.intro or "",
            tendency_type=tendency_type,
            is_following=False,
        )

    @staticmethod
    def _create_related_pod_dto(notification: Notification):
        """알림의 관련 파티 DTO 생성"""
        if not notification.related_pod:
            return None

        # PodDtoService를 사용하여 변환
        return PodDtoService.convert_to_dto(notification.related_pod)

    @staticmethod
    def _parse_related_id(related_id) -> int | None:
        """related_id를 int로 변환"""
        if related_id is None:
            return None
        try:
            return int(related_id)
        except (ValueError, TypeError):
            return None
