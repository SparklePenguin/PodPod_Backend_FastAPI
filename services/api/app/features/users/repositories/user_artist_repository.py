"""
사용자 선호 아티스트 Repository
"""

from typing import List

from app.features.users.models import PreferredArtist
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


class UserArtistRepository:
    """사용자 선호 아티스트 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 선호 아티스트 ID 목록 조회
    async def get_preferred_artist_ids(self, user_id: int) -> List[int]:
        """사용자의 선호 아티스트 ID 목록 조회"""
        result = await self._session.execute(
            select(PreferredArtist.artist_id).where(PreferredArtist.user_id == user_id)
        )
        # scalars().all()은 동기 메서드이지만 이미 비동기 실행 후이므로 블로킹되지 않음
        # 명시적으로 리스트로 변환하여 반환
        return list(result.scalars().all())

    # - MARK: 선호 아티스트 추가
    async def add_preferred_artist(self, user_id: int, artist_id: int) -> None:
        """단일 선호 아티스트 추가"""
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
        # Service 레이어에서 commit 관리

    # - MARK: 선호 아티스트 제거
    async def remove_preferred_artist(self, user_id: int, artist_id: int) -> None:
        """단일 선호 아티스트 제거"""
        await self._session.execute(
            delete(PreferredArtist).where(
                PreferredArtist.user_id == user_id,
                PreferredArtist.artist_id == artist_id,
            )
        )
        # Service 레이어에서 commit 관리

    # - MARK: 선호 아티스트 일괄 제거
    async def remove_all_preferred_artists(self, user_id: int) -> None:
        """사용자의 모든 선호 아티스트 제거"""
        await self._session.execute(
            delete(PreferredArtist).where(PreferredArtist.user_id == user_id)
        )
        # Service 레이어에서 commit 관리

    # - MARK: 선호 아티스트 일괄 추가
    async def add_preferred_artists(self, user_id: int, artist_ids: List[int]) -> None:
        """여러 선호 아티스트를 한 번에 추가 (중복 체크 포함)"""
        # 기존 선호 아티스트 조회
        existing_ids = await self.get_preferred_artist_ids(user_id)
        # set 연산은 동기 작업이지만 선호 아티스트는 3명까지이므로 문제 없음
        existing_set = set(existing_ids)

        # 새로운 아티스트만 추가 (리스트 컴프리헨션은 동기 작업이지만 선호 아티스트는 3명까지이므로 문제 없음)
        new_artists = [
            PreferredArtist(user_id=user_id, artist_id=artist_id)
            for artist_id in artist_ids
            if artist_id not in existing_set
        ]

        if new_artists:
            # add_all은 동기 메서드이지만 세션에 추가만 하므로 블로킹되지 않음
            self._session.add_all(new_artists)
            # Service 레이어에서 commit 관리
