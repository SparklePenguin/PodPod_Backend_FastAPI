"""
사용자 알림 설정 CRUD
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import time

from app.models.user_notification_settings import UserNotificationSettings


class UserNotificationSettingsCRUD:
    """사용자 알림 설정 CRUD"""

    async def get_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> Optional[UserNotificationSettings]:
        """사용자 ID로 알림 설정 조회"""
        result = await db.execute(
            select(UserNotificationSettings).where(
                UserNotificationSettings.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_default_settings(
        self, db: AsyncSession, user_id: int
    ) -> UserNotificationSettings:
        """기본 알림 설정 생성"""
        settings = UserNotificationSettings(
            user_id=user_id,
            notice_enabled=True,
            pod_enabled=True,
            community_enabled=True,
            chat_enabled=True,
            do_not_disturb_enabled=False,
            do_not_disturb_start=None,
            do_not_disturb_end=None,
            marketing_enabled=False,
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        return settings

    async def get_or_create(
        self, db: AsyncSession, user_id: int
    ) -> UserNotificationSettings:
        """알림 설정 조회 또는 생성"""
        settings = await self.get_by_user_id(db, user_id)
        if not settings:
            settings = await self.create_default_settings(db, user_id)
        return settings

    async def update_settings(
        self,
        db: AsyncSession,
        user_id: int,
        notice_enabled: Optional[bool] = None,
        pod_enabled: Optional[bool] = None,
        community_enabled: Optional[bool] = None,
        chat_enabled: Optional[bool] = None,
        do_not_disturb_enabled: Optional[bool] = None,
        do_not_disturb_start: Optional[str] = None,
        do_not_disturb_end: Optional[str] = None,
        marketing_enabled: Optional[bool] = None,
    ) -> UserNotificationSettings:
        """알림 설정 업데이트"""
        settings = await self.get_or_create(db, user_id)

        # 제공된 필드만 업데이트
        if notice_enabled is not None:
            settings.notice_enabled = notice_enabled
        if pod_enabled is not None:
            settings.pod_enabled = pod_enabled
        if community_enabled is not None:
            settings.community_enabled = community_enabled
        if chat_enabled is not None:
            settings.chat_enabled = chat_enabled
        if do_not_disturb_enabled is not None:
            settings.do_not_disturb_enabled = do_not_disturb_enabled
        if do_not_disturb_start is not None:
            # "HH:MM" 문자열을 time 객체로 변환
            if do_not_disturb_start:
                hour, minute = map(int, do_not_disturb_start.split(":"))
                settings.do_not_disturb_start = time(hour=hour, minute=minute)
            else:
                settings.do_not_disturb_start = None
        if do_not_disturb_end is not None:
            # "HH:MM" 문자열을 time 객체로 변환
            if do_not_disturb_end:
                hour, minute = map(int, do_not_disturb_end.split(":"))
                settings.do_not_disturb_end = time(hour=hour, minute=minute)
            else:
                settings.do_not_disturb_end = None
        if marketing_enabled is not None:
            settings.marketing_enabled = marketing_enabled

        await db.commit()
        await db.refresh(settings)
        return settings


# 싱글톤 인스턴스
user_notification_settings_crud = UserNotificationSettingsCRUD()
