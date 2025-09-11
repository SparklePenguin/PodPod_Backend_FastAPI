from typing import List, Optional
from app.schemas.artist_sync_dto import ArtistsSyncDto
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import json
import os

from app.models.artist import Artist
from app.models.artist_unit import ArtistUnit
from app.models.artist_image import ArtistImage
from app.models.artist_name import ArtistName


class ArtistCRUD:
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
        self, page: int = 1, page_size: int = 20, is_active: bool = True
    ) -> tuple[List[Artist], int]:
        """아티스트 목록 조회 (페이지네이션 및 is_active 필터링 지원)

        Returns:
            tuple[List[Artist], int]: (아티스트 목록, 전체 개수)
        """
        # 기본 쿼리
        query = select(Artist).options(
            selectinload(Artist.images),
            selectinload(Artist.names),
        )

        # 전체 개수 조회 (is_active는 Artist에 없으므로 필터 없이 계산)
        count_query = select(func.count()).select_from(Artist)

        total_count_result = await self.db.execute(count_query)
        total_count = total_count_result.scalar()

        # 페이지네이션 적용
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        artists = result.scalars().all()

        return artists, total_count

    # - MARK: MVP·BLIP 동기화
    async def sync_from_blip_and_mvp(self) -> dict:
        """BLIP 데이터 기반으로 유닛 → 메인(그룹) → 멤버 아티스트를 동기화합니다.
        - 식별: blip unitId, artistId 사용
        - 모든 아티스트는 unit_id(=unitId)로 엮임
        - 각 아티스트별 images, names는 unitId 기준으로 재생성
        """
        # 파일 경로들
        blip_file_path = "mvp/blip_artists.json"
        mvp_file_path = "mvp/artists.json"

        # 파일 존재 확인
        if not os.path.exists(blip_file_path):
            raise FileNotFoundError(
                f"BLIP JSON 파일을 찾을 수 없습니다: {blip_file_path}"
            )
        if not os.path.exists(mvp_file_path):
            raise FileNotFoundError(
                f"MVP JSON 파일을 찾을 수 없습니다: {mvp_file_path}"
            )

        # 데이터 로드
        with open(blip_file_path, "r", encoding="utf-8") as f:
            blip_data = json.load(f)
        with open(mvp_file_path, "r", encoding="utf-8") as f:
            mvp_data = json.load(f)

        # 이름 정규화 함수
        def _norm(s: str) -> str:
            return (s or "").strip().lower()

        mvp_names = set(_norm(x) for x in mvp_data.get("artists", []))

        unit_created_count = 0
        unit_updated_count = 0
        artist_created_count = 0
        artist_updated_count = 0

        # BLIP 아티스트 순회 (각 항목 = 하나의 유닛 + 메인 + 멤버들)
        for item in blip_data:
            blip_unit_id = item.get("unitId")
            blip_artist_id = item.get("artistId")
            unit_name = (item.get("blipName") or "").strip()
            is_filter_flag = bool(item.get("isFilter", 0))

            # 필수 식별자 체크: unitId와 메인 artistId가 없으면 스킵
            if not blip_unit_id:
                continue

            is_active = _norm(unit_name) in mvp_names
            if is_active:
                mvp_names.remove(unit_name)

            type = "group" if (item.get("members") or []) else "solo"

            # 1) 유닛 업서트: blip_unit_id로 식별
            unit_q = await self.db.execute(
                select(ArtistUnit).where(
                    ArtistUnit.blip_unit_id == blip_unit_id,
                )
            )
            unit = unit_q.scalar_one_or_none()

            if unit is None:
                unit = ArtistUnit(
                    name=unit_name,
                    type=type,
                    is_filter=is_filter_flag,
                    is_active=is_active,
                    blip_unit_id=blip_unit_id,
                    blip_artist_id=blip_artist_id,
                )
                self.db.add(unit)
                unit_created_count += 1
                await self.db.flush()
            else:
                # 업데이트
                unit.name = unit_name or unit.name
                unit.type = type
                unit.is_active = is_active
                unit.is_filter = is_filter_flag
                unit.blip_unit_id = blip_unit_id
                unit.blip_artist_id = blip_artist_id
                unit_updated_count += 1

            # 1) 그룹(메인) 아티스트 업서트: blip_unit_id + blip_artist_id로 식별
            rep_artist_q = await self.db.execute(
                select(Artist).where(
                    Artist.blip_unit_id == blip_unit_id,
                    Artist.blip_artist_id == blip_artist_id,
                )
            )
            rep_artist = rep_artist_q.scalar_one_or_none()

            if rep_artist is None:
                rep_artist = Artist(
                    name=unit_name,
                    unit_id=unit.id,
                    blip_unit_id=blip_unit_id,
                    blip_artist_id=blip_artist_id,
                )
                self.db.add(rep_artist)
                artist_created_count += 1
                await self.db.flush()
            else:
                # 갱신
                rep_artist.name = unit_name or rep_artist.name
                rep_artist.unit_id = unit.id
                rep_artist.blip_unit_id = blip_unit_id
                rep_artist.blip_artist_id = blip_artist_id or rep_artist.blip_artist_id
                artist_updated_count += 1

            # 2) ArtistUnit 업서트: rep_artist.id에 연결
            unit.artist_id = rep_artist.id
            self.db.add(unit)

            # 3) 메인 아티스트 images/names 재생성 (blip_unit_id + blip_artist_id 기준)
            await self.db.execute(
                ArtistImage.__table__.delete().where(
                    (ArtistImage.blip_unit_id == blip_unit_id)
                    & (ArtistImage.blip_artist_id == blip_artist_id)
                )
            )
            await self.db.execute(
                ArtistName.__table__.delete().where(
                    (ArtistName.blip_unit_id == blip_unit_id)
                    & (ArtistName.blip_artist_id == blip_artist_id)
                )
            )

            image = item.get("image") or {}
            self.db.add(
                ArtistImage(
                    artist_id=rep_artist.id,
                    unit_id=unit.id,
                    path=image.get("path"),
                    file_id=None,  # BLIP fileId는 보관하지 않음
                    is_animatable=bool(image.get("isAnimatable", False)),
                    size=image.get("size"),
                    blip_unit_id=blip_unit_id,
                    blip_artist_id=blip_artist_id,
                )
            )

            for name in item.get("names") or []:
                self.db.add(
                    ArtistName(
                        artist_id=rep_artist.id,
                        unit_id=unit.id,
                        code=(name or {}).get("code") or "",
                        name=(name or {}).get("name") or "",
                        blip_unit_id=blip_unit_id,
                        blip_artist_id=blip_artist_id,
                    )
                )

            # 4) 멤버 아티스트 업서트 및 images/names 재생성
            for member in item.get("members") or []:
                blip_member_artist_id = (member or {}).get("artistId")
                member_name = (member or {}).get("name") or ""
                # 멤버 식별자 체크: artistId 없으면 스킵
                if not blip_member_artist_id:
                    continue

                mem_q = await self.db.execute(
                    select(Artist).where(
                        Artist.blip_unit_id == blip_unit_id,
                        Artist.blip_artist_id == blip_member_artist_id,
                    )
                )
                member_artist = mem_q.scalar_one_or_none()

                if member_artist is None:
                    member_artist = Artist(
                        name=member_name,
                        unit_id=unit.id,
                        blip_unit_id=blip_unit_id,
                        blip_artist_id=blip_member_artist_id,
                    )
                    self.db.add(member_artist)
                    artist_created_count += 1
                    await self.db.flush()
                else:
                    member_artist.name = member_name or member_artist.name
                    member_artist.unit_id = unit.id
                    member_artist.blip_unit_id = blip_unit_id
                    member_artist.blip_artist_id = (
                        blip_member_artist_id or member_artist.blip_artist_id
                    )
                    artist_updated_count += 1

                # 멤버 images/names 재생성
                await self.db.execute(
                    ArtistImage.__table__.delete().where(
                        (ArtistImage.artist_id == blip_member_artist_id)
                        & (ArtistImage.unit_id == blip_unit_id)
                    )
                )
                await self.db.execute(
                    ArtistName.__table__.delete().where(
                        (ArtistName.artist_id == blip_member_artist_id)
                        & (ArtistName.unit_id == blip_unit_id)
                    )
                )

                mem_img = (member or {}).get("image") or {}
                self.db.add(
                    ArtistImage(
                        artist_id=member_artist.id,
                        unit_id=unit.id,
                        path=mem_img.get("path"),
                        file_id=None,  # BLIP fileId는 보관하지 않음
                        is_animatable=bool(mem_img.get("isAnimatable", False)),
                        size=mem_img.get("size"),
                        blip_unit_id=blip_unit_id,
                        blip_artist_id=blip_member_artist_id,
                    )
                )

                for n in (member or {}).get("names") or []:
                    self.db.add(
                        ArtistName(
                            artist_id=member_artist.id,
                            unit_id=unit.id,
                            code=(n or {}).get("code") or "",
                            name=(n or {}).get("name") or "",
                            blip_unit_id=blip_unit_id,
                            blip_artist_id=blip_member_artist_id,
                        )
                    )

        await self.db.commit()

        return ArtistsSyncDto(
            artist_created=artist_created_count,
            artist_updated=artist_updated_count,
            unit_created=unit_created_count,
            unit_updated=unit_updated_count,
            left_mvp_names=list(mvp_names),
        )
