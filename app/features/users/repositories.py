from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.pods.models.pod.pod_application import PodApplication
from app.features.users.models import (
    PreferredArtist,
    User,
    UserBlock,
    UserNotificationSettings,
    UserReport,
)
from app.features.users.schemas import UpdateUserNotificationSettingsRequest


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # 사용자 조회
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    # (내부 사용) 이메일로 사용자 조회
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    # (내부 사용) 이메일과 프로바이더로 사용자 조회
    async def get_by_email_and_provider(
        self, email: str, auth_provider: str
    ) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email, User.auth_provider == auth_provider)
        )
        return result.scalar_one_or_none()

    # (내부 사용) auth_provider와 auth_provider_id로 사용자 조회
    async def get_by_auth_provider_id(
        self, auth_provider: str, auth_provider_id: str
    ) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(
                User.auth_provider == auth_provider,
                User.auth_provider_id == auth_provider_id,
            )
        )
        return result.scalar_one_or_none()

    # 사용자 생성
    async def create(self, user_data: Dict[str, Any]) -> User:
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    # (내부 사용) 사용자 목록 조회
    async def get_all(self) -> List[User]:
        result = await self.db.execute(select(User))
        return list(result.scalars().all())

    # 사용자 프로필 업데이트
    async def update_profile(
        self, user_id: int, update_data: Dict[str, Any]
    ) -> Optional[User]:
        if not update_data:
            return await self.get_by_id(user_id)

        # None이 아닌 값들만 필터링
        filtered_data = {k: v for k, v in update_data.items() if v is not None}

        if not filtered_data:
            return await self.get_by_id(user_id)

        # updated_at 자동 업데이트를 위해 추가
        from datetime import datetime, timezone

        filtered_data["updated_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(User).where(User.id == user_id).values(**filtered_data)
        )
        await self.db.commit()
        return await self.get_by_id(user_id)

    # 사용자 선호 아티스트 조회 (아티스트 ID 목록 반환)
    async def get_preferred_artist_ids(self, user_id: int) -> List[int]:
        result = await self.db.execute(
            select(PreferredArtist.artist_id).where(PreferredArtist.user_id == user_id)
        )
        return list(result.scalars().all())

    # 사용자 선호 아티스트 추가
    async def add_preferred_artist(self, user_id: int, artist_id: int) -> None:
        # 이미 존재하면 중복 추가 방지
        exists_q = await self.db.execute(
            select(PreferredArtist).where(
                PreferredArtist.user_id == user_id,
                PreferredArtist.artist_id == artist_id,
            )
        )
        if exists_q.scalar_one_or_none() is not None:
            return

        preferred_artist = PreferredArtist(user_id=user_id, artist_id=artist_id)
        self.db.add(preferred_artist)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            # FK/유니크 충돌 시 무시 (상위 레이어에서 검증 권장)
            return

    # 사용자 선호 아티스트 제거
    async def remove_preferred_artist(self, user_id: int, artist_id: int) -> None:
        await self.db.execute(
            delete(PreferredArtist).where(
                PreferredArtist.user_id == user_id,
                PreferredArtist.artist_id == artist_id,
            )
        )
        await self.db.commit()

    # FCM 토큰 업데이트
    async def update_fcm_token(self, user_id: int, fcm_token: Optional[str]) -> None:
        """사용자의 FCM 토큰 업데이트"""
        from datetime import datetime, timezone

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(fcm_token=fcm_token, updated_at=datetime.now(timezone.utc))
        )
        await self.db.commit()

    # 사용자 삭제
    async def delete(self, user_id: int) -> None:
        """
        사용자 삭제
        - ON DELETE CASCADE로 인해 관련 데이터(preferred_artists, follows 등)도 함께 삭제됨
        """
        # pod_applications.reviewed_by FK 해제
        await self.db.execute(
            update(PodApplication)
            .where(PodApplication.reviewed_by == user_id)
            .values(reviewed_by=None)
        )

        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()


class UserNotificationSettingsRepository:
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
                    from datetime import datetime

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

        return bool(category_mapping[notification_category])


class UserBlockRepository:
    """사용자 차단 CRUD 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_block(
        self, blocker_id: int, blocked_id: int
    ) -> Optional[UserBlock]:
        """사용자 차단 생성"""
        try:
            # 자기 자신을 차단하는지 확인
            if blocker_id == blocked_id:
                return None

            # 이미 차단하고 있는지 확인
            existing_block = await self.get_block(blocker_id, blocked_id)
            if existing_block:
                return existing_block

            block = UserBlock(blocker_id=blocker_id, blocked_id=blocked_id)
            self.db.add(block)
            await self.db.commit()
            await self.db.refresh(block)
            return block
        except Exception:
            await self.db.rollback()
            return None

    async def delete_block(self, blocker_id: int, blocked_id: int) -> bool:
        """사용자 차단 해제"""
        try:
            block = await self.get_block(blocker_id, blocked_id)
            if not block:
                return False

            await self.db.delete(block)
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False

    async def get_block(self, blocker_id: int, blocked_id: int) -> Optional[UserBlock]:
        """특정 차단 관계 조회"""
        query = select(UserBlock).where(
            and_(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def check_block_exists(self, blocker_id: int, blocked_id: int) -> bool:
        """차단 관계 존재 여부 확인"""
        query = select(UserBlock).where(
            and_(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_blocked_users(
        self, blocker_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Tuple[User, datetime]], int]:
        """차단한 사용자 목록 조회"""
        offset = (page - 1) * size

        # 차단한 사용자 목록 조회
        query = (
            select(User, UserBlock.created_at)
            .join(UserBlock, User.id == UserBlock.blocked_id)
            .where(UserBlock.blocker_id == blocker_id)
            .order_by(desc(UserBlock.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        blocked_data_raw = result.all()

        # Row 객체를 Tuple로 변환
        blocked_data: List[Tuple[User, datetime]] = [
            (row[0], row[1]) for row in blocked_data_raw
        ]

        # 총 차단 수 조회
        count_query = select(func.count(UserBlock.id)).where(
            UserBlock.blocker_id == blocker_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        return blocked_data, total_count

    async def delete_all_by_user(self, user_id: int) -> None:
        """특정 사용자와 관련된 모든 차단 관계 삭제"""
        # 해당 사용자가 차단한 경우와 차단당한 경우 모두 삭제
        await self.db.execute(
            delete(UserBlock).where(
                or_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == user_id)
            )
        )
        await self.db.commit()


class UserReportRepository:
    """사용자 신고 CRUD 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        report_types: List[int],
        reason: Optional[str],
        blocked: bool,
    ) -> Optional[UserReport]:
        """사용자 신고 생성"""
        try:
            # 자기 자신을 신고하는지 확인
            if reporter_id == reported_user_id:
                return None

            report = UserReport(
                reporter_id=reporter_id,
                reported_user_id=reported_user_id,
                report_types=report_types,
                reason=reason,
                blocked=blocked,
            )
            self.db.add(report)
            await self.db.commit()
            await self.db.refresh(report)
            return report
        except Exception:
            await self.db.rollback()
            return None

    async def get_report_by_id(self, report_id: int) -> Optional[UserReport]:
        """신고 ID로 조회"""
        query = select(UserReport).where(UserReport.id == report_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_reports_by_reporter(
        self, reporter_id: int, page: int = 1, size: int = 20
    ) -> tuple[List[UserReport], int]:
        """신고자가 작성한 신고 목록 조회"""
        offset = (page - 1) * size

        query = (
            select(UserReport)
            .where(UserReport.reporter_id == reporter_id)
            .order_by(desc(UserReport.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        reports = result.scalars().all()

        # 총 개수 조회
        count_query = select(func.count(UserReport.id)).where(
            UserReport.reporter_id == reporter_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        return list(reports), total_count

    async def get_reports_by_reported_user(
        self, reported_user_id: int, page: int = 1, size: int = 20
    ) -> tuple[List[UserReport], int]:
        """신고당한 사용자의 신고 목록 조회"""
        offset = (page - 1) * size

        query = (
            select(UserReport)
            .where(UserReport.reported_user_id == reported_user_id)
            .order_by(desc(UserReport.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        reports = result.scalars().all()

        # 총 개수 조회
        count_query = select(func.count(UserReport.id)).where(
            UserReport.reported_user_id == reported_user_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        return list(reports), total_count
