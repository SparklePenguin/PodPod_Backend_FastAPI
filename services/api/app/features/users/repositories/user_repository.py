from datetime import datetime, timezone
from typing import Any, Dict, List

from app.features.users.models import PreferredArtist, User
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
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

    # - MARK: 선호 아티스트 ID 목록 조회
    async def get_preferred_artist_ids(self, user_id: int) -> List[int]:
        result = await self._session.execute(
            select(PreferredArtist.artist_id).where(PreferredArtist.user_id == user_id)
        )
        return list(result.scalars().all())

    # - MARK: 선호 아티스트 추가
    async def add_preferred_artist(self, user_id: int, artist_id: int) -> None:
        # 이미 존재하면 중복 추가 방지
        exists_q = await self._session.execute(
            select(PreferredArtist).where(
                PreferredArtist.user_id == user_id,
                PreferredArtist.artist_id == artist_id,
            )
        )
        if exists_q.scalar_one_or_none() is not None:
            return

        preferred_artist = PreferredArtist(user_id=user_id, artist_id=artist_id)
        self._session.add(preferred_artist)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            # FK/유니크 충돌 시 무시 (상위 레이어에서 검증 권장)
            return

    # - MARK: 선호 아티스트 제거
    async def remove_preferred_artist(self, user_id: int, artist_id: int) -> None:
        await self._session.execute(
            delete(PreferredArtist).where(
                PreferredArtist.user_id == user_id,
                PreferredArtist.artist_id == artist_id,
            )
        )
        await self._session.commit()

    # - MARK: 선호 아티스트 일괄 제거
    async def remove_all_preferred_artists(self, user_id: int) -> None:
        """사용자의 모든 선호 아티스트 제거"""
        await self._session.execute(
            delete(PreferredArtist).where(PreferredArtist.user_id == user_id)
        )
        await self._session.commit()

    # - MARK: 선호 아티스트 일괄 추가
    async def add_preferred_artists(self, user_id: int, artist_ids: List[int]) -> None:
        """여러 선호 아티스트를 한 번에 추가 (중복 체크 포함)"""
        # 기존 선호 아티스트 조회
        existing_ids = await self.get_preferred_artist_ids(user_id)
        existing_set = set(existing_ids)

        # 새로운 아티스트만 추가
        new_artists = [
            PreferredArtist(user_id=user_id, artist_id=artist_id)
            for artist_id in artist_ids
            if artist_id not in existing_set
        ]

        if new_artists:
            self._session.add_all(new_artists)
            try:
                await self._session.commit()
            except IntegrityError:
                await self._session.rollback()
                # 개별 추가로 폴백
                for artist in new_artists:
                    try:
                        self._session.add(artist)
                        await self._session.commit()
                    except IntegrityError:
                        await self._session.rollback()

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
