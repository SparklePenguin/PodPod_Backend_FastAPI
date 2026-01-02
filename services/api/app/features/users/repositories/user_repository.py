from datetime import datetime, timezone
from typing import Any, Dict

from app.features.users.models import User
from sqlalchemy import select, update
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
        return result.scalar_one_or_none()

    # - MARK: OAuth 프로바이더 ID로 사용자 조회
    async def get_by_auth_provider_id(
        self, auth_provider: str, auth_provider_id: str
    ) -> User | None:
        result = await self._session.execute(
            select(User).where(
                User.auth_provider == auth_provider,
                User.auth_provider_id == auth_provider_id,
            )
        )
        return result.scalar_one_or_none()

    # - MARK: 사용자 생성
    async def create(self, user_data: Dict[str, Any]) -> User:
        user = User(**user_data)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    # - MARK: 프로필 업데이트
    async def update_profile(
        self, user_id: int, update_data: Dict[str, Any]
    ) -> User | None:
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
        await self._session.commit()
        return await self.get_by_id(user_id)

    # - MARK: FCM 토큰 업데이트
    async def update_fcm_token(self, user_id: int, fcm_token: str | None) -> None:
        """사용자의 FCM 토큰 업데이트"""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(fcm_token=fcm_token, updated_at=datetime.now(timezone.utc))
        )
        await self._session.commit()

    # - MARK: 사용자 정보 업데이트
    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> User | None:
        """사용자 정보 업데이트 (is_del 플래그 및 정보 업데이트)"""
        # updated_at 자동 업데이트
        updates["updated_at"] = datetime.now(timezone.utc)

        await self._session.execute(
            update(User).where(User.id == user_id).values(**updates)
        )
        await self._session.commit()
        return await self.get_by_id(user_id)

    # - MARK: 약관 동의 업데이트
    async def update_terms_accepted(
        self, user_id: int, terms_accepted: bool
    ) -> User | None:
        """약관 동의 상태 업데이트"""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                terms_accepted=terms_accepted, updated_at=datetime.now(timezone.utc)
            )
        )
        await self._session.commit()
        return await self.get_by_id(user_id)
