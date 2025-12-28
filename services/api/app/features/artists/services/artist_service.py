from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import PageDto
from app.features.artists.exceptions import ArtistNotFoundException
from app.features.artists.repositories.artist_repository import ArtistRepository
from app.features.artists.schemas import ArtistDto


class ArtistService:
    def __init__(self, db: AsyncSession):
        self.artist_repo = ArtistRepository(db)

    # - MARK: 아티스트 조회
    async def get_artist(self, artist_id: int) -> ArtistDto:
        artist = await self.artist_repo.get_by_id(artist_id)
        if not artist:
            raise ArtistNotFoundException(artist_id)
        return ArtistDto.model_validate(artist, from_attributes=True)

    # - MARK: 아티스트 목록 조회
    async def get_artists(
        self, page: int = 1, size: int = 20, is_active: bool = True
    ) -> PageDto[ArtistDto]:
        """아티스트 목록 조회 (페이지네이션 및 필터링 지원)"""
        artists, total_count = await self.artist_repo.get_all(
            page=page, size=size, is_active=is_active
        )

        artist_dtos = [
            ArtistDto.model_validate(artist, from_attributes=True) for artist in artists
        ]

        return PageDto.create(
            items=artist_dtos, page=page, size=size, total_count=total_count
        )
