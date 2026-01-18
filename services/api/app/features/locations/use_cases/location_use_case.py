"""Location Use Case - 비즈니스 로직 처리"""

import json
from collections import defaultdict
from typing import List

from app.features.locations.repositories.location_repository import LocationRepository
from app.features.locations.schemas import LocationDto
from sqlalchemy.ext.asyncio import AsyncSession


class LocationUseCase:
    """지역 정보 Use Case"""

    def __init__(self, session: AsyncSession, location_repo: LocationRepository):
        self._session = session
        self._location_repo = location_repo

    # - MARK: 모든 지역 정보 조회
    async def get_all_locations(self) -> List[LocationDto]:
        """모든 지역 정보 조회 (인기 지역 포함)"""
        locations = await self._location_repo.get_all_locations()

        # 일반 지역 정보
        all_locations = [
            self._to_dto(location) for location in locations
        ]

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
        return popular_locations + filtered_all_locations

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

        return self._to_dto(location)

    # - MARK: 지역 정보 생성
    async def create_location(
        self, main_location: str, sub_locations: List[str]
    ) -> LocationDto:
        """지역 정보 생성"""
        location = await self._location_repo.create_location(
            main_location, sub_locations
        )
        await self._session.commit()
        await self._session.refresh(location)

        return self._to_dto(location)

    # - MARK: 지역 정보 수정
    async def update_location(
        self, location_id: int, main_location: str, sub_locations: List[str]
    ) -> LocationDto | None:
        """지역 정보 수정"""
        location = await self._location_repo.update_location(
            location_id, main_location, sub_locations
        )
        await self._session.commit()

        if not location:
            return None

        await self._session.refresh(location)
        return self._to_dto(location)

    # - MARK: 지역 정보 삭제
    async def delete_location(self, location_id: int) -> bool:
        """지역 정보 삭제"""
        result = await self._location_repo.delete_location(location_id)
        await self._session.commit()
        return result

    # - MARK: 인기 지역 조회
    async def get_popular_locations(self) -> List[LocationDto]:
        """인기 지역 조회 - 팟티의 address, sub_address에서 지역 매칭하여 카운트"""
        # 모든 팟티의 address, sub_address 조회
        pod_addresses = await self._location_repo.get_pod_addresses()

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
                            break
                    else:
                        continue
                    break

        # 카운트 기준으로 정렬하여 상위 10개 선택
        sorted_locations = sorted(
            location_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # LocationDto 형태로 변환
        popular_locations = []
        for main_location, _ in sorted_locations:
            for location in locations:
                if location.main_location == main_location:
                    popular_locations.append(self._to_dto(location))
                    break

        return popular_locations

    # - MARK: Location -> LocationDto 변환
    def _to_dto(self, location) -> LocationDto:
        """Location 모델을 LocationDto로 변환"""
        sub_locations = json.loads(location.sub_locations or "[]")
        return LocationDto(
            id=location.id,
            main_location=location.main_location,
            sub_locations=sub_locations,
        )
