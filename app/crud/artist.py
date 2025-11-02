from typing import List, Optional
from app.schemas.artist_sync_dto import ArtistsSyncDto
from sqlalchemy import select, func, and_
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
            if unit.artist_id:
                artist = await self.get_by_id(unit.artist_id)
                if artist:
                    artists.append(artist)

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

        result = ArtistsSyncDto(
            artist_created=artist_created_count,
            artist_updated=artist_updated_count,
            unit_created=unit_created_count,
            unit_updated=unit_updated_count,
            left_mvp_names=list(mvp_names),
        )
        return result.model_dump(by_alias=True)

    async def get_artist_image_by_file_id(self, file_id: str) -> Optional[ArtistImage]:
        """file_id로 아티스트 이미지를 조회합니다.

        Args:
            file_id: 파일 ID

        Returns:
            Optional[ArtistImage]: 조회된 이미지 또는 None
        """
        try:
            print(f"DEBUG: get_artist_image_by_file_id 호출됨, file_id: {file_id}")
            result = await self.db.execute(
                select(ArtistImage).where(ArtistImage.file_id == file_id)
            )
            image = result.scalar_one_or_none()
            print(f"DEBUG: 쿼리 결과: {image is not None}")
            if image:
                print(f"DEBUG: 찾은 이미지 ID: {image.id}")
            return image
        except Exception as e:
            print(f"DEBUG: get_artist_image_by_file_id 오류: {str(e)}")
            return None

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
        artist_units = result.scalars().all()

        return artist_units, total_count

    async def update_single_artist_image(
        self, image_id: int, image_data: dict
    ) -> tuple[bool, str]:
        """단일 아티스트 이미지를 업데이트합니다.

        Args:
            image_id: 이미지 ID
            image_data: 업데이트할 이미지 데이터

        Returns:
            tuple[bool, str]: (성공 여부, 메시지)
        """
        try:
            # 이미지 존재 확인
            result = await self.db.execute(
                select(ArtistImage).where(ArtistImage.id == image_id)
            )
            image = result.scalar_one_or_none()

            if not image:
                return False, f"이미지를 찾을 수 없습니다. ID: {image_id}"

            # 이미지 데이터 업데이트
            if "path" in image_data:
                image.path = image_data["path"]
            if "file_id" in image_data:
                image.file_id = image_data["file_id"]
            if "is_animatable" in image_data:
                image.is_animatable = image_data["is_animatable"]
            if "size" in image_data:
                image.size = image_data["size"]

            self.db.add(image)
            await self.db.commit()

            return True, f"이미지 ID {image_id}가 성공적으로 업데이트되었습니다."

        except Exception as e:
            await self.db.rollback()
            return False, f"이미지 업데이트 실패: {str(e)}"

    async def create_artist_image(
        self, artist_id: int, image_data: dict
    ) -> tuple[bool, str, Optional[ArtistImage]]:
        """아티스트에 새로운 이미지를 생성하거나 기존 이미지를 업데이트합니다.

        Args:
            artist_id: 아티스트 ID
            image_data: 생성할 이미지 데이터

        Returns:
            tuple[bool, str, Optional[ArtistImage]]: (성공 여부, 메시지, 생성/업데이트된 이미지)
        """
        try:
            # 아티스트 존재 확인
            artist = await self.get_by_id(artist_id)
            if not artist:
                return False, f"아티스트를 찾을 수 없습니다. ID: {artist_id}", None

            # file_id로 기존 이미지가 있는지 확인
            existing_image = None
            if image_data.get("file_id"):
                print(f"DEBUG: file_id로 기존 이미지 찾기: {image_data['file_id']}")
                existing_image = await self.get_artist_image_by_file_id(
                    image_data["file_id"]
                )
                print(f"DEBUG: 기존 이미지 찾음: {existing_image is not None}")
                if existing_image:
                    print(f"DEBUG: 기존 이미지 ID: {existing_image.id}")

            if existing_image:
                # 기존 이미지 업데이트
                if "path" in image_data and image_data["path"]:
                    existing_image.path = image_data["path"]
                if "file_id" in image_data and image_data["file_id"]:
                    existing_image.file_id = image_data["file_id"]
                if "is_animatable" in image_data:
                    existing_image.is_animatable = image_data["is_animatable"]
                if "size" in image_data and image_data["size"]:
                    existing_image.size = image_data["size"]

                await self.db.commit()
                await self.db.refresh(existing_image)

                return (
                    True,
                    f"아티스트 {artist.name}의 이미지가 성공적으로 업데이트되었습니다.",
                    existing_image,
                )
            else:
                # 새로운 이미지 생성
                new_image = ArtistImage(
                    artist_id=artist_id,
                    unit_id=artist.unit_id,
                    path=image_data.get("path"),
                    file_id=image_data.get("file_id"),
                    is_animatable=image_data.get("is_animatable", False),
                    size=image_data.get("size"),
                    blip_unit_id=artist.blip_unit_id,
                    blip_artist_id=artist.blip_artist_id,
                )

                self.db.add(new_image)
                await self.db.commit()
                await self.db.refresh(new_image)

                return (
                    True,
                    f"아티스트 {artist.name}의 이미지가 성공적으로 생성되었습니다.",
                    new_image,
                )

        except Exception as e:
            await self.db.rollback()
            return False, f"이미지 생성/업데이트 실패: {str(e)}", None
