import json
from collections import defaultdict
from typing import List

from app.features.locations.repositories.location_repository import LocationRepository
from app.features.locations.schemas import LocationDto
from app.features.pods.models.pod.pod import Pod
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class LocationService:
    """지역 정보 Service"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._location_repo = LocationRepository(session)

    # - MARK: 모든 지역 정보 조회
    async def get_all_locations(self) -> List[LocationDto]:
        """모든 지역 정보 조회 (인기 지역 포함)"""
        locations = await self._location_repo.get_all_locations()

        # 일반 지역 정보
        all_locations = []
        for location in locations:
            sub_locations_str = location.sub_locations or "[]"
            sub_locations = json.loads(sub_locations_str)
            all_locations.append(
                LocationDto(
                    id=location.id,
                    main_location=location.main_location,
                    sub_locations=sub_locations,
                )
            )

        # 인기 지역 정보
        popular_locations = await self.get_popular_locations()

        # 인기 지역의 main_location 목록 추출
        popular_main_locations = {loc.main_location for loc in popular_locations}

        # 일반 지역에서 인기 지역과 중복되지 않는 것만 필터링
        filtered_all_locations = [
            loc
            for loc in all_locations
            if loc.main_location not in popular_main_locations
        ]

        # 인기 지역을 맨 앞에 추가
        combined_locations = popular_locations + filtered_all_locations

        return combined_locations

    # - MARK: 주요 지역으로 지역 정보 조회
    async def get_location_by_main_location(
        self, main_location: str
    ) -> LocationDto | None:
        """주요 지역으로 지역 정보 조회"""
        location = await self._location_repo.get_location_by_main_location(
            main_location
        )

        if not location:
            return None

        sub_locations = json.loads(location.sub_locations or "[]")
        return LocationDto(
            id=location.id,
            main_location=location.main_location,
            sub_locations=sub_locations,
        )

    # - MARK: 지역 정보 생성
    async def create_location(
        self, main_location: str, sub_locations: List[str]
    ) -> LocationDto:
        """지역 정보 생성"""
        location = await self._location_repo.create_location(
            main_location, sub_locations
        )

        sub_locations_list = json.loads(location.sub_locations or "[]")
        return LocationDto(
            id=location.id,
            main_location=location.main_location,
            sub_locations=sub_locations_list,
        )

    # - MARK: 지역 정보 수정
    async def update_location(
        self, location_id: int, main_location: str, sub_locations: List[str]
    ) -> LocationDto | None:
        """지역 정보 수정"""
        location = await self._location_repo.update_location(
            location_id, main_location, sub_locations
        )

        if not location:
            return None

        sub_locations_list = json.loads(location.sub_locations or "[]")
        return LocationDto(
            id=location.id,
            main_location=location.main_location,
            sub_locations=sub_locations_list,
        )

    # - MARK: 지역 정보 삭제
    async def delete_location(self, location_id: int) -> bool:
        """지역 정보 삭제"""
        return await self._location_repo.delete_location(location_id)

    # - MARK: 인기 지역 조회
    async def get_popular_locations(self) -> List[LocationDto]:
        """인기 지역 조회 - 팟티의 address, sub_address에서 지역 매칭하여 카운트"""
        # 모든 팟티의 address, sub_address 조회
        result = await self._session.execute(
            select(Pod.address, Pod.sub_address).where(Pod.is_active)
        )
        pod_addresses = result.fetchall()

        # 모든 지역 정보 조회
        locations = await self._location_repo.get_all_locations()

        # 지역별 카운트를 위한 딕셔너리
        location_counts = defaultdict(int)

        # 각 팟티의 주소에서 지역 매칭
        for address, sub_address in pod_addresses:
            # address와 sub_address를 하나의 문자열로 합치기
            full_address = f"{address} {sub_address or ''}".strip()

            # 각 지역의 sub_locations와 매칭
            for location in locations:
                sub_locations = json.loads(location.sub_locations or "[]")
                for sub_location in sub_locations:
                    # sub_location을 "·"로 분리하여 각각 확인
                    sub_parts = sub_location.split("·")
                    for part in sub_parts:
                        part = part.strip()
                        if part and part in full_address:
                            location_counts[location.main_location] += 1
                            break  # 한 지역에서 매칭되면 다른 sub_location은 확인하지 않음
                    else:
                        continue  # break가 실행되지 않았으면 계속
                    break  # 내부 for문에서 break가 실행되었으면 외부 for문도 break

        # 카운트 기준으로 정렬하여 상위 10개 선택
        sorted_locations = sorted(
            location_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # LocationDto 형태로 변환
        popular_locations = []
        for main_location, count in sorted_locations:
            # 해당 main_location의 sub_locations 찾기
            for location in locations:
                if location.main_location == main_location:
                    sub_locations = json.loads(location.sub_locations or "[]")
                    popular_locations.append(
                        LocationDto(
                            id=location.id,
                            main_location=main_location,
                            sub_locations=sub_locations,
                        )
                    )
                    break

        return popular_locations
