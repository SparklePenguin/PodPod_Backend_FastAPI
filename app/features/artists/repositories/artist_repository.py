from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.artists.models import Artist, ArtistUnit


class ArtistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: 아티스트 조회
    async def get_by_unit_id(self, unit_id: int) -> Optional[Artist]:
        """unit_id로 아티스트 찾기"""
        result = await self.db.execute(select(Artist).where(Artist.unit_id == unit_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, artist_id: int) -> Optional[Artist]:
        """artist_id로 아티스트 찾기"""
        result = await self.db.execute(
            select(Artist)
            .options(
                selectinload(Artist.images),
                selectinload(Artist.names),
            )
            .where(Artist.id == artist_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Artist]:
        """이름으로 아티스트 찾기"""
        result = await self.db.execute(select(Artist).where(Artist.name == name))
        return result.scalar_one_or_none()

    # - MARK: 아티스트 목록 조회
    async def get_all(
        self, page: int = 1, size: int = 20, is_active: bool = True
    ) -> tuple[List[Artist], int]:
        """아티스트 목록 조회 (페이지네이션 및 is_active 필터링 지원)
        ArtistUnit을 기준으로 각 unit의 artist_id에 해당하는 대표 아티스트만 반환

        Returns:
            tuple[List[Artist], int]: (아티스트 목록, 전체 개수)
        """
        # ArtistUnit을 기준으로 조회 (is_active 필터 적용)
        artist_units, total_count = await self.get_artist_units_with_names(
            page=page, size=size, is_active=is_active
        )

        # 각 unit의 artist_id로 Artist 조회
        artists = []
        for unit in artist_units:
            unit_artist_id = getattr(unit, "artist_id", None)
            if unit_artist_id is not None:
                artist = await self.get_by_id(unit_artist_id)
                if artist:
                    artists.append(artist)

        return artists, total_count

    # NOTE: 아래 메서드들은 services/scraping 마이크로서비스로 이전되었습니다.
    # - sync_from_blip_and_mvp() -> services/scraping/app/repositories/artist_repository.py
    # - get_artist_image_by_file_id() -> services/scraping/app/repositories/artist_repository.py

    async def get_artist_units_with_names(
        self, page: int = 1, size: int = 20, is_active: bool = True
    ) -> tuple[List[ArtistUnit], int]:
        """ArtistUnit과 연결된 Artist 이름을 조회합니다.

        Args:
            page: 페이지 번호
            size: 페이지 크기
            is_active: 활성화 상태 필터

        Returns:
            tuple[List[ArtistUnit], int]: (ArtistUnit 리스트, 총 개수)
        """
        # ArtistUnit 조회 (artist_id가 있는 것만)
        query = (
            select(ArtistUnit)
            .where(
                and_(
                    ArtistUnit.is_active == is_active, ArtistUnit.artist_id.isnot(None)
                )
            )
            .order_by(ArtistUnit.id)
        )

        # 총 개수 조회
        count_result = await self.db.execute(
            select(func.count(ArtistUnit.id)).where(
                and_(
                    ArtistUnit.is_active == is_active, ArtistUnit.artist_id.isnot(None)
                )
            )
        )
        total_count = count_result.scalar()

        # 페이지네이션 적용
        offset = (page - 1) * size
        result = await self.db.execute(query.offset(offset).limit(size))
        artist_units = list(result.scalars().all())

        # total_count가 None일 수 있으므로 기본값 0 사용
        total_count_value = total_count if total_count is not None else 0

        return artist_units, total_count_value

    # NOTE: 아래 메서드들은 services/scraping 마이크로서비스로 이전되었습니다.
    # - update_single_artist_image() -> services/scraping/app/repositories/artist_repository.py (제거됨)
    # - create_artist_image() -> services/scraping/app/repositories/artist_repository.py
