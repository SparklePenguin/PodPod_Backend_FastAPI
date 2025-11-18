"""
사용자 알림 설정 CRUD
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.user_notification_settings import UserNotificationSettings
from app.schemas.user_notification_settings import UpdateUserNotificationSettingsRequest


class UserNotificationSettingsCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[UserNotificationSettings]:
        """사용자 ID로 알림 설정 조회"""
        result = await self.db.execute(
            select(UserNotificationSettings).where(
                UserNotificationSettings.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_default_settings(self, user_id: int) -> UserNotificationSettings:
        """기본 알림 설정 생성"""
        settings = UserNotificationSettings(
            user_id=user_id,
            notice_enabled=True,
            pod_enabled=True,
            community_enabled=True,
            chat_enabled=True,
            do_not_disturb_enabled=False,
            marketing_enabled=False,
        )
        self.db.add(settings)
        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def update_settings(
        self, user_id: int, update_data: UpdateUserNotificationSettingsRequest
    ) -> Optional[UserNotificationSettings]:
        """알림 설정 업데이트"""
        settings = await self.get_by_user_id(user_id)
        if not settings:
            return None

        # 업데이트할 필드만 적용
        update_dict = update_data.model_dump(exclude_unset=True, by_alias=True)

        # 필드명 매핑 (camelCase -> snake_case)
        field_mapping = {
            "wakeUpAlarm": "notice_enabled",
            "busAlert": "chat_enabled",
            "partyAlert": "pod_enabled",
            "communityAlert": "community_enabled",
            "productAlarm": "marketing_enabled",
            "doNotDisturbEnabled": "do_not_disturb_enabled",
            "startTime": "do_not_disturb_start",
            "endTime": "do_not_disturb_end",
            "marketingEnabled": "marketing_enabled",
        }

        for key, value in update_dict.items():
            if key in field_mapping and value is not None:
                db_field = field_mapping[key]
                if key in ["startTime", "endTime"] and value:
                    # timestamp를 Time 객체로 변환
                    from datetime import datetime, time

                    try:
                        # timestamp를 datetime으로 변환 후 time 추출
                        dt = datetime.fromtimestamp(
                            value / 1000
                        )  # milliseconds to seconds
                        time_obj = dt.time()
                        setattr(settings, db_field, time_obj)
                    except (ValueError, TypeError):
                        # 파싱 실패 시 무시
                        pass
                else:
                    setattr(settings, db_field, value)

        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def should_send_notification(
        self, user_id: int, notification_category: str
    ) -> bool:
        """알림 전송 여부 확인"""
        settings = await self.get_by_user_id(user_id)
        if not settings:
            return True  # 설정이 없으면 기본적으로 전송

        # 카테고리별 설정 확인
        category_mapping = {
            "POD": settings.pod_enabled,
            "COMMUNITY": settings.community_enabled,
            "NOTICE": settings.notice_enabled,
        }

        if notification_category not in category_mapping:
            return True

        return category_mapping[notification_category]
