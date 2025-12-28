from typing import List

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.artists.models import Artist, ArtistUnit


class ArtistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_unit_id(self, unit_id: int) -> Artist | None:
        """unit_id로 아티스트 찾기"""
        result = await self.db.execute(
            select(Artist)
            .options(selectinload(Artist.images), selectinload(Artist.names))
            .where(Artist.unit_id == unit_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, artist_id: int) -> Artist | None:
        """artist_id로 아티스트 찾기"""
        result = await self.db.execute(
            select(Artist)
            .options(selectinload(Artist.images), selectinload(Artist.names))
            .where(Artist.id == artist_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Artist | None:
        """이름으로 아티스트 찾기"""
        result = await self.db.execute(
            select(Artist)
            .options(selectinload(Artist.images), selectinload(Artist.names))
            .where(Artist.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, page: int = 1, size: int = 20, is_active: bool = True
    ) -> tuple[List[Artist], int]:
        """아티스트 목록 조회 (ArtistUnit을 기준으로 각 unit의 artist_id에 해당하는 대표 아티스트만 반환)"""
        # ArtistUnit을 기준으로 조회 (is_active 필터 적용)
        artist_units, total_count = await self.get_artist_units_with_names(
            page=page, size=size, is_active=is_active
        )

        # artist_id 리스트 추출 (순서 유지를 위해 딕셔너리 사용)
        artist_id_to_unit = {
            unit.artist_id: unit
            for unit in artist_units
            if getattr(unit, "artist_id", None) is not None
        }
        artist_ids = list(artist_id_to_unit.keys())

        # N+1 문제 방지: 한 번의 쿼리로 모든 Artist 조회 (관계 포함)
        if not artist_ids:
            return [], total_count

        query = (
            select(Artist)
            .options(selectinload(Artist.images), selectinload(Artist.names))
            .where(Artist.id.in_(artist_ids))
        )
        result = await self.db.execute(query)
        artists_dict = {artist.id: artist for artist in result.scalars().all()}

        # artist_units의 순서대로 artists 정렬
        artists = [
            artists_dict[unit.artist_id]
            for unit in artist_units
            if unit.artist_id in artists_dict
        ]

        return artists, total_count

    async def get_artist_units_with_names(
        self, page: int = 1, size: int = 20, is_active: bool = True
    ) -> tuple[List[ArtistUnit], int]:
        """ArtistUnit과 연결된 Artist 이름을 조회"""
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
