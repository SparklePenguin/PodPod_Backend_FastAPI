from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.features.locations.models.location import Location
import json


class LocationCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_locations(self) -> List[Location]:
        """모든 지역 정보 조회"""
        result = await self.db.execute(select(Location))
        return list(result.scalars().all())

    async def get_location_by_main_location(
        self, main_location: str
    ) -> Location | None:
        """주요 지역으로 지역 정보 조회"""
        result = await self.db.execute(
            select(Location).where(Location.main_location == main_location)
        )
        return result.scalar_one_or_none()

    async def create_location(
        self, main_location: str, sub_locations: List[str]
    ) -> Location:
        """지역 정보 생성"""
        location = Location(
            main_location=main_location,
            sub_locations=json.dumps(sub_locations, ensure_ascii=False),
        )
        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)
        return location

    async def update_location(
        self, location_id: int, main_location: str, sub_locations: List[str]
    ) -> Location | None:
        """지역 정보 수정"""
        result = await self.db.execute(
            select(Location).where(Location.id == location_id)
        )
        location = result.scalar_one_or_none()

        if location:
            setattr(location, "main_location", main_location)
            setattr(
                location, "sub_locations", json.dumps(sub_locations, ensure_ascii=False)
            )
            await self.db.commit()
            await self.db.refresh(location)

        return location

    async def delete_location(self, location_id: int) -> bool:
        """지역 정보 삭제"""
        result = await self.db.execute(
            select(Location).where(Location.id == location_id)
        )
        location = result.scalar_one_or_none()

        if location:
            await self.db.delete(location)
            await self.db.commit()
            return True

        return False
