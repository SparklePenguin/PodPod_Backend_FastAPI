from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.artist import ArtistCRUD
from app.schemas.artist import ArtistDto
from app.schemas.common import ErrorResponse


class ArtistService:
    def __init__(self, db: AsyncSession):
        self.artist_crud = ArtistCRUD(db)

    # - MARK: 아티스트 조회
    async def get_artist(self, artist_id: int) -> ArtistDto:
        artist = await self.artist_crud.get_by_id(artist_id)
        if not artist:
            return None
        return ArtistDto.model_validate(
            artist,
            from_attributes=True,
        )

    # - MARK: 아티스트 목록 조회
    async def get_artists(self) -> List[ArtistDto]:
        artists = await self.artist_crud.get_all()
        return [
            ArtistDto.model_validate(
                artist,
                from_attributes=True,
            )
            for artist in artists
        ]

    # - MARK: (내부용) MVP 아티스트 생성
    async def create_mvp_artists(self) -> List[ArtistDto]:
        """MVP 아티스트들을 생성"""
        artists = await self.artist_crud.create_mvp_artists()
        return [
            ArtistDto.model_validate(
                artist,
                from_attributes=True,
            )
            for artist in artists
        ]

    # - MARK: (내부용) JSON 파일에서 아티스트 생성
    async def create_artists_from_json(self, json_file_path: str) -> List[ArtistDto]:
        """JSON 파일에서 아티스트들을 생성"""
        artists = await self.artist_crud.create_from_json(json_file_path)
        return [
            ArtistDto.model_validate(
                artist,
                from_attributes=True,
            )
            for artist in artists
        ]
