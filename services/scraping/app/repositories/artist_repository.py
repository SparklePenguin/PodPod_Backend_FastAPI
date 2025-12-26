import json
import os
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models import Artist, ArtistImage, ArtistName, ArtistUnit


class ArtistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: 아티스트 조회
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

    async def get_artist_image_by_file_id(self, file_id: str) -> Optional[ArtistImage]:
        """file_id로 아티스트 이미지를 조회합니다."""
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

    async def create_artist_image(
        self, artist_id: int, image_data: dict
    ) -> tuple[bool, str, Optional[ArtistImage]]:
        """아티스트에 새로운 이미지를 생성하거나 기존 이미지를 업데이트합니다."""
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

    # - MARK: MVP·BLIP 동기화
    async def sync_from_blip_and_mvp(self) -> dict:
        """BLIP 데이터 기반으로 유닛 → 메인(그룹) → 멤버 아티스트를 동기화합니다."""
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

        # BLIP 아티스트 순회
        for item in blip_data:
            blip_unit_id = item.get("unitId")
            blip_artist_id = item.get("artistId")
            unit_name = (item.get("blipName") or "").strip()
            is_filter_flag = bool(item.get("isFilter", 0))

            if not blip_unit_id:
                continue

            is_active = _norm(unit_name) in mvp_names
            if is_active:
                mvp_names.remove(unit_name)

            type = "group" if (item.get("members") or []) else "solo"

            # 1) 유닛 업서트
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
                unit.name = unit_name or unit.name  # type: ignore
                unit.type = type  # type: ignore
                unit.is_active = is_active  # type: ignore
                unit.is_filter = is_filter_flag  # type: ignore
                unit.blip_unit_id = blip_unit_id
                unit.blip_artist_id = blip_artist_id
                unit_updated_count += 1

            # 2) 그룹(메인) 아티스트 업서트
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
                rep_artist.name = unit_name or rep_artist.name  # type: ignore
                rep_artist.unit_id = unit.id
                rep_artist.blip_unit_id = blip_unit_id
                rep_artist.blip_artist_id = blip_artist_id or rep_artist.blip_artist_id
                artist_updated_count += 1

            unit.artist_id = rep_artist.id
            self.db.add(unit)

            # 3) 메인 아티스트 images/names 재생성
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
                    file_id=None,
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
                    member_artist.name = member_name or member_artist.name  # type: ignore
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
                        file_id=None,
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

        return {
            "artist_created": artist_created_count,
            "artist_updated": artist_updated_count,
            "unit_created": unit_created_count,
            "unit_updated": unit_updated_count,
            "left_mvp_names": list(mvp_names),
        }
