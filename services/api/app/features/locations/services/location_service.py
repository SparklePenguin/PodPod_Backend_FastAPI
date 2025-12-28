import json
import os
from collections import defaultdict
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.locations.repositories.location_repository import LocationCRUD
from app.features.locations.schemas import LocationDto, LocationResponse
from app.features.pods.models.pod.pod import Pod


class LocationService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._location_repo = LocationCRUD(db)

    async def get_all_locations(self) -> List[LocationResponse]:
        """모든 지역 정보 조회 (인기 지역 포함)"""
        locations = await self._location_repo.get_all_locations()

        # 일반 지역 정보
        all_locations = []
        for location in locations:
            location_sub_locations = getattr(location, 'sub_locations', '[]') or '[]'
            location_main_location = getattr(location, 'main_location', '') or ''
            sub_locations = json.loads(location_sub_locations)
            all_locations.append(
                LocationResponse(
                    main_location=location_main_location, sub_locations=sub_locations
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

    async def get_location_by_main_location(
        self, main_location: str
    ) -> LocationResponse | None:
        """주요 지역으로 지역 정보 조회"""
        location = await self._location_repo.get_location_by_main_location(main_location)

        if not location:
            return None

        location_sub_locations = getattr(location, 'sub_locations', '[]') or '[]'
        location_main_location = getattr(location, 'main_location', '') or ''
        sub_locations = json.loads(location_sub_locations)
        return LocationResponse(
            main_location=location_main_location, sub_locations=sub_locations
        )

    async def create_location(
        self, main_location: str, sub_locations: List[str]
    ) -> LocationDto:
        """지역 정보 생성"""
        location = await self._location_repo.create_location(main_location, sub_locations)

        location_sub_locations = getattr(location, 'sub_locations', '[]') or '[]'
        location_id = getattr(location, 'id', 0) or 0
        location_main_location = getattr(location, 'main_location', '') or ''
        sub_locations_list = json.loads(location_sub_locations)
        return LocationDto(
            id=location_id,
            main_location=location_main_location,
            sub_locations=sub_locations_list,
        )

    async def update_location(
        self, location_id: int, main_location: str, sub_locations: List[str]
    ) -> LocationDto | None:
        """지역 정보 수정"""
        location = await self._location_repo.update_location(
            location_id, main_location, sub_locations
        )

        if not location:
            return None

        location_sub_locations = getattr(location, 'sub_locations', '[]') or '[]'
        location_id_val = getattr(location, 'id', 0) or 0
        location_main_location = getattr(location, 'main_location', '') or ''
        sub_locations_list = json.loads(location_sub_locations)
        return LocationDto(
            id=location_id_val,
            main_location=location_main_location,
            sub_locations=sub_locations_list,
        )

    async def delete_location(self, location_id: int) -> bool:
        """지역 정보 삭제"""
        return await self._location_repo.delete_location(location_id)

    async def create_locations_from_json(self) -> List[LocationDto]:
        """JSON 파일에서 지역 데이터를 읽어서 생성"""
        # JSON 파일 경로 (프로젝트 루트 기준)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, "../../..")
        json_file_path = os.path.abspath(
            os.path.join(project_root, "mvp/locations.json")
        )

        # JSON 파일 읽기
        with open(json_file_path, "r", encoding="utf-8") as file:
            locations_data = json.load(file)

        created_locations = []

        for location_data in locations_data:
            main_location = location_data["mainLocation"]
            sub_locations = location_data["subLocations"]

            # 이미 존재하는지 확인
            existing_location = await self._location_repo.get_location_by_main_location(
                main_location
            )

            if not existing_location:
                # 새로 생성
                location = await self._location_repo.create_location(main_location, sub_locations)
                location_sub_locations = getattr(location, 'sub_locations', '[]') or '[]'
                location_id = getattr(location, 'id', 0) or 0
                location_main_location = getattr(location, 'main_location', '') or ''
                sub_locations_list = json.loads(location_sub_locations)
                created_locations.append(
                    LocationDto(
                        id=location_id,
                        main_location=location_main_location,
                        sub_locations=sub_locations_list,
                    )
                )

        return created_locations

    async def get_popular_locations(self) -> List[LocationResponse]:
        """인기 지역 조회 - 팟티의 address, sub_address에서 지역 매칭하여 카운트"""
        # 모든 팟티의 address, sub_address 조회
        result = await self._db.execute(
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
                location_sub_locations = getattr(location, 'sub_locations', '[]') or '[]'
                sub_locations = json.loads(location_sub_locations)
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

        # PopularLocationResponse 형태로 변환
        popular_locations = []
        for main_location, count in sorted_locations:
            # 해당 main_location의 sub_locations 찾기
            for location in locations:
                location_main_location = getattr(location, 'main_location', '') or ''
                if location_main_location == main_location:
                    location_sub_locations = getattr(location, 'sub_locations', '[]') or '[]'
                    sub_locations = json.loads(location_sub_locations)
                    popular_locations.append(
                        LocationResponse(
                            main_location=main_location, sub_locations=sub_locations
                        )
                    )
                    break

        return popular_locations
