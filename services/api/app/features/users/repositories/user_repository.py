from datetime import datetime, timezone
from typing import Any, Dict

from app.features.users.models import User
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 사용자 ID로 조회
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    # - MARK: 이메일로 사용자 조회
    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    # - MARK: 이메일과 OAuth 프로바이더로 사용자 조회
    async def get_by_email_and_provider(
        self, email: str, auth_provider: str | None
    ) -> User | None:
        """이메일과 OAuth 제공자로 사용자 조회 (같은 이메일, 다른 제공자 구분용)"""
        if auth_provider:
            # OAuth 로그인인 경우: email + provider 조합으로 조회
            result = await self._session.execute(
                select(User).where(
                    and_(User.email == email, User.auth_provider == auth_provider)
                )
            )
        else:
            # 일반 로그인인 경우: email만으로 조회 (auth_provider가 NULL인 사용자)
            result = await self._session.execute(
                select(User).where(
                    and_(User.email == email, User.auth_provider.is_(None))
                )
            )
        return result.scalars().first()

    # - MARK: OAuth 프로바이더 ID로 사용자 조회
    async def get_by_auth_provider_id(
        self, auth_provider: str, auth_provider_id: str
    ) -> User | None:
        result = await self._session.execute(
            select(User).where(
                and_(
                    User.auth_provider == auth_provider,
                    User.auth_provider_id == auth_provider_id,
                )
            )
        )
        return result.scalar_one_or_none()

    # - MARK: 사용자 생성 (커밋 없음)
    async def create(self, user_data: Dict[str, Any]) -> User:
        """사용자 생성 (커밋은 use_case에서 처리)"""
        user = User(**user_data)
        self._session.add(user)
        return user

    # - MARK: 프로필 업데이트 (커밋 없음)
    async def update_profile(
        self, user_id: int, update_data: Dict[str, Any]
    ) -> User | None:
        """프로필 업데이트 (커밋은 use_case에서 처리)"""
        if not update_data:
            return await self.get_by_id(user_id)

        # None이 아닌 값들만 필터링
        filtered_data = {k: v for k, v in update_data.items() if v is not None}

        if not filtered_data:
            return await self.get_by_id(user_id)

        # updated_at 자동 업데이트
        filtered_data["updated_at"] = datetime.now(timezone.utc)

        await self._session.execute(
            update(User).where(User.id == user_id).values(**filtered_data)
        )
        return await self.get_by_id(user_id)

    # - MARK: FCM 토큰 업데이트 (커밋 없음)
    async def update_fcm_token(self, user_id: int, fcm_token: str | None) -> None:
        """사용자의 FCM 토큰 업데이트 (커밋은 use_case에서 처리)"""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(fcm_token=fcm_token, updated_at=datetime.now(timezone.utc))
        )

    # - MARK: 사용자 정보 업데이트 (커밋 없음)
    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> User | None:
        """사용자 정보 업데이트 (커밋은 use_case에서 처리)"""
        # updated_at 자동 업데이트
        updates["updated_at"] = datetime.now(timezone.utc)

        await self._session.execute(
            update(User).where(User.id == user_id).values(**updates)
        )
        return await self.get_by_id(user_id)

    # - MARK: 약관 동의 업데이트 (커밋 없음)
    async def update_terms_accepted(
        self, user_id: int, terms_accepted: bool
    ) -> User | None:
        """약관 동의 상태 업데이트 (커밋은 use_case에서 처리)"""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                terms_accepted=terms_accepted, updated_at=datetime.now(timezone.utc)
            )
        )
        return await self.get_by_id(user_id)

    # - MARK: 사용자 소프트 삭제 (커밋 없음)
    async def soft_delete_user(self, user_id: int) -> None:
        """사용자 소프트 삭제 처리 (커밋은 use_case에서 처리)"""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                is_del=True,
                is_active=False,
                nickname=None,  # 개인정보 삭제
                email=None,
                profile_image=None,
                intro=None,
                fcm_token=None,
                terms_accepted=False,  # 약관 동의 초기화
            )
        )

    # - MARK: 사용자 성향 타입 조회
    async def get_user_tendency_type(self, user_id: int) -> str:
        """사용자의 성향 타입 조회"""
        from app.features.tendencies.models import UserTendencyResult

        result = await self._session.execute(
            select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
        )
        tendency = result.scalar_one_or_none()
        return (
            str(tendency.tendency_type) if tendency and tendency.tendency_type else ""
        )
