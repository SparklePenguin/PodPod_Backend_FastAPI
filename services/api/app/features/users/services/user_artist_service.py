"""
사용자 선호 아티스트 Service
"""

from typing import List

from app.features.artists.exceptions import ArtistNotFoundException
from app.features.artists.repositories.artist_repository import ArtistRepository
from app.features.artists.schemas import ArtistDto
from app.features.users.repositories.user_artist_repository import (
    UserArtistRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession


class UserArtistService:
    """사용자 선호 아티스트 Service"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_artist_repo = UserArtistRepository(session)
        self._artist_repo = ArtistRepository(session)

    # - MARK: 선호 아티스트 조회
    async def get_preferred_artists(self, user_id: int) -> List[ArtistDto]:
        """사용자의 선호 아티스트 목록 조회"""
        # 아티스트 ID 목록 가져오기
        artist_ids = await self._user_artist_repo.get_preferred_artist_ids(user_id)

        if not artist_ids:
            return []

        # 모든 아티스트를 한 번에 조회 (artist_repository 사용)
        artists = await self._artist_repo.get_by_ids(artist_ids)

        # ID 순서 유지를 위한 딕셔너리 생성 (동기 작업이지만 선호 아티스트는 3명까지이므로 문제 없음)
        artist_dict = {artist.id: artist for artist in artists}

        # 원래 순서대로 반환 (동기 작업이지만 선호 아티스트는 3명까지이므로 문제 없음)
        return [
            ArtistDto.model_validate(artist_dict[artist_id], from_attributes=True)
            for artist_id in artist_ids
            if artist_id in artist_dict
        ]

    # - MARK: 선호 아티스트 업데이트 (추가/제거)
    async def update_preferred_artists(
        self, user_id: int, artist_ids: List[int]
    ) -> List[ArtistDto]:
        """선호 아티스트 목록을 완전히 교체하여 업데이트"""
        try:
            if not artist_ids:
                # 빈 리스트면 모든 선호 아티스트 제거
                await self._user_artist_repo.remove_all_preferred_artists(user_id)
                await self._session.commit()
                return []

            # 모든 아티스트를 한 번에 조회하여 존재 확인 (artist_repository 사용)
            artists = await self._artist_repo.get_by_ids(artist_ids)

            # set 연산은 동기 작업이지만 선호 아티스트는 3명까지이므로 문제 없음
            found_ids = {artist.id for artist in artists}
            missing_ids = set(artist_ids) - found_ids

            if missing_ids:
                raise ArtistNotFoundException(list(missing_ids)[0])

            # 기존 선호 아티스트 모두 제거 (bulk 작업)
            await self._user_artist_repo.remove_all_preferred_artists(user_id)

            # 새로운 선호 아티스트 일괄 추가 (bulk 작업)
            await self._user_artist_repo.add_preferred_artists(user_id, artist_ids)

            # 트랜잭션 커밋
            await self._session.commit()

        except Exception:
            # 에러 발생 시 롤백
            await self._session.rollback()
            raise

        # 업데이트된 선호 아티스트 목록 반환
        return await self.get_preferred_artists(user_id)
