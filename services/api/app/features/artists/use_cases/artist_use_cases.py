"""아티스트 관련 Use Cases"""

from app.common.schemas import PageDto
from app.features.artists.exceptions import ArtistNotFoundException
from app.features.artists.repositories.artist_repository import ArtistRepository
from app.features.artists.schemas import ArtistDto
from app.features.artists.services.artist_dto_service import ArtistDtoService
from sqlalchemy.ext.asyncio import AsyncSession


class GetArtistUseCase:
    """단일 아티스트 조회 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.artist_repo = ArtistRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(self, artist_id: int) -> ArtistDto:
        """아티스트 조회"""
        artist = await self.artist_repo.get_by_id(artist_id)
        if not artist:
            raise ArtistNotFoundException(artist_id)
        return self.dto_service.to_artist_dto(artist)


class GetArtistsUseCase:
    """아티스트 목록 조회 Use Case"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self.artist_repo = ArtistRepository(session)
        self.dto_service = ArtistDtoService()

    async def execute(
        self, page: int = 1, size: int = 20, is_active: bool = True
    ) -> PageDto[ArtistDto]:
        """아티스트 목록 조회 (페이지네이션 및 필터링 지원)"""
        artists, total_count = await self.artist_repo.get_all(
            page=page, size=size, is_active=is_active
        )

        artist_dtos = self.dto_service.to_artist_dtos(artists)

        return PageDto.create(
            items=artist_dtos, page=page, size=size, total_count=total_count
        )
