from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import os

from app.models.artist import Artist


class ArtistCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, artist_id: int) -> Optional[Artist]:
        result = await self.db.execute(
            text("SELECT * FROM artists WHERE id = :artist_id"),
            {"artist_id": artist_id},
        )
        return result.fetchone()

    async def get_all(self) -> List[Artist]:
        result = await self.db.execute(text("SELECT * FROM artists"))
        return result.fetchall()

    async def create(self, artist_data: dict) -> Artist:
        """아티스트 생성"""
        artist = Artist(**artist_data)
        self.db.add(artist)
        await self.db.commit()
        await self.db.refresh(artist)
        return artist

    async def get_by_name(self, name: str) -> Optional[Artist]:
        """이름으로 아티스트 찾기"""
        result = await self.db.execute(
            text("SELECT * FROM artists WHERE name = :name"),
            {"name": name},
        )
        return result.fetchone()

    async def create_from_json(
        self, json_file_path: str = "mvp_artists.json"
    ) -> List[Artist]:
        """JSON 파일에서 아티스트들을 생성"""
        created_artists = []

        # JSON 파일 읽기
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {json_file_path}")

        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        artists_list = data.get("artists", [])

        for artist_name in artists_list:
            # 이미 존재하는지 확인
            existing_artist = await self.get_by_name(artist_name)
            if existing_artist:
                print(f"아티스트 '{artist_name}'은 이미 존재합니다.")
                continue

            # 새 아티스트 생성
            artist_data = {"name": artist_name, "profile_image": None}  # 기본값

            artist = await self.create(artist_data)
            created_artists.append(artist)
            print(f"아티스트 '{artist_name}'이 생성되었습니다.")

        return created_artists

    async def create_mvp_artists(self) -> List[Artist]:
        """MVP 아티스트들을 생성 (기본 JSON 파일 사용)"""
        return await self.create_from_json("mvp_artists.json")
