import json
from typing import List, Tuple

from app.features.locations.models import Location
from app.features.pods.models import Pod
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class LocationRepository:
    """지역 정보 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 모든 지역 정보 조회
    async def get_all_locations(self) -> List[Location]:
        """모든 지역 정보 조회"""
        result = await self._session.execute(select(Location))
        return list(result.scalars().all())

    # - MARK: 주요 지역으로 지역 정보 조회
    async def get_location_by_main_location(
        self, main_location: str
    ) -> Location | None:
        """주요 지역으로 지역 정보 조회"""
        result = await self._session.execute(
            select(Location).where(Location.main_location == main_location)
        )
        return result.scalar_one_or_none()

    # - MARK: 지역 정보 생성
    async def create_location(
        self, main_location: str, sub_locations: List[str]
    ) -> Location:
        """지역 정보 생성"""
        location = Location(
            main_location=main_location,
            sub_locations=json.dumps(sub_locations, ensure_ascii=False),
        )
        self._session.add(location)
        await self._session.commit()
        await self._session.refresh(location)
        return location

    # - MARK: 지역 정보 수정
    async def update_location(
        self, location_id: int, main_location: str, sub_locations: List[str]
    ) -> Location | None:
        """지역 정보 수정"""
        await self._session.execute(
            update(Location)
            .where(Location.id == location_id)
            .values(
                main_location=main_location,
                sub_locations=json.dumps(sub_locations, ensure_ascii=False),
            )
        )
        await self._session.commit()
        return await self.get_location_by_id(location_id)

    # - MARK: 지역 정보 ID로 조회
    async def get_location_by_id(self, location_id: int) -> Location | None:
        """지역 정보 ID로 조회"""
        result = await self._session.execute(
            select(Location).where(Location.id == location_id)
        )
        return result.scalar_one_or_none()

    # - MARK: 지역 정보 삭제
    async def delete_location(self, location_id: int) -> bool:
        """지역 정보 삭제"""
        location = await self.get_location_by_id(location_id)
        if not location:
            return False

        await self._session.delete(location)
        await self._session.commit()
        return True

    # - MARK: 파티 주소 조회
    async def get_pod_addresses(self) -> List[Tuple[str, str | None]]:
        """모든 활성 파티의 address, sub_address 조회 (PodDetail에서)"""
        from app.features.pods.models import PodDetail

        result = await self._session.execute(
            select(PodDetail.address, PodDetail.sub_address)
            .join(Pod, Pod.id == PodDetail.pod_id)
            .where(Pod.is_del == False)
        )
        return result.fetchall()
