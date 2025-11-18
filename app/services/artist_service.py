from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.artist import ArtistCRUD
from app.schemas.artist import ArtistDto, ArtistSimpleDto
from app.schemas.common import PageDto


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

    # - MARK: 아티스트 목록 조회 (간소화)
    async def get_artists_simple(
        self, page: int = 1, size: int = 20, is_active: bool = True
    ) -> PageDto[ArtistSimpleDto]:
        """아티스트 목록 조회 (간소화 - ArtistUnit의 artist_id에 해당하는 아티스트 이름만)"""
        artist_units, total_count = await self.artist_crud.get_artist_units_with_names(
            page=page, size=size, is_active=is_active
        )

        # ArtistUnit의 artist_id에 해당하는 아티스트 이름만 추출
        simple_artists = []
        for unit in artist_units:
            if unit.artist_id:  # artist_id가 있는 경우만
                # 해당 artist_id로 아티스트 조회
                artist = await self.artist_crud.get_by_id(unit.artist_id)
                if artist:
                    simple_artists.append(
                        ArtistSimpleDto(
                            unit_id=unit.id, artist_id=artist.id, name=artist.name
                        )
                    )

        # 페이지네이션 계산
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto[ArtistSimpleDto](
            items=simple_artists,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    # - MARK: 아티스트 목록 조회
    async def get_artists(
        self, page: int = 1, size: int = 20, is_active: bool = True
    ) -> PageDto[ArtistDto]:
        """아티스트 목록 조회 (페이지네이션 및 필터링 지원)"""
        artists, total_count = await self.artist_crud.get_all(
            page=page, size=size, is_active=is_active
        )

        artist_dtos = [
            ArtistDto.model_validate(
                artist,
                from_attributes=True,
            )
            for artist in artists
        ]

        # 페이지네이션 정보 계산
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto[ArtistDto](
            items=artist_dtos,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    # 사용하지 않는 내부 생성/업데이트 메서드 제거됨

    # - MARK: (내부용) BLIP+MVP 병합 동기화
    async def sync_blip_and_mvp(self) -> dict:
        """BLIP 전체 데이터와 MVP 이름 목록을 병합하여 DB에 동기화"""
        return await self.artist_crud.sync_from_blip_and_mvp()
