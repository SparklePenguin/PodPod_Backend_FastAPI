from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.preferred_artist import PreferredArtist
from typing import List, Optional, Dict, Any


class UserCRUD:
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
        return result.scalars().all()

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
        return result.scalars().all()

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
        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()
