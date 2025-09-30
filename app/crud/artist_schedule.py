from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.artist_schedule import (
    ArtistSchedule,
    ScheduleMember,
    ScheduleContent,
    ScheduleType,
)
from app.models.artist import Artist
from app.models.artist_name import ArtistName
from app.schemas.artist_schedule import (
    ArtistScheduleCreateRequest,
    ScheduleMemberCreateRequest,
    ScheduleContentCreateRequest,
)


class ArtistScheduleCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_schedule(
        self, request: ArtistScheduleCreateRequest
    ) -> ArtistSchedule:
        """아티스트 스케줄 생성"""
        # 스케줄 생성
        schedule = ArtistSchedule(
            artist_id=request.artist_id,
            unit_id=request.unit_id,
            artist_ko_name=request.artist_ko_name,
            type=request.type,
            start_time=request.start_time,
            end_time=request.end_time,
            text=request.text,
            title=request.title,
            channel=request.channel,
            location=request.location,
        )

        self.db.add(schedule)
        await self.db.flush()  # ID를 얻기 위해 flush

        # 멤버들 생성
        for member_req in request.members:
            member = ScheduleMember(
                schedule_id=schedule.id,
                artist_id=member_req.artist_id,
                ko_name=member_req.ko_name,
                en_name=member_req.en_name,
            )
            self.db.add(member)

        # 콘텐츠들 생성
        for content_req in request.contents:
            content = ScheduleContent(
                schedule_id=schedule.id,
                type=content_req.type,
                path=content_req.path,
                title=content_req.title,
            )
            self.db.add(content)

        await self.db.commit()
        await self.db.refresh(schedule)

        return schedule

    async def get_schedule_by_id(self, schedule_id: int) -> Optional[ArtistSchedule]:
        """ID로 스케줄 조회"""
        query = (
            select(ArtistSchedule)
            .options(
                selectinload(ArtistSchedule.members),
                selectinload(ArtistSchedule.contents),
            )
            .where(ArtistSchedule.id == schedule_id)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_schedules(
        self,
        page: int = 1,
        page_size: int = 20,
        artist_id: Optional[int] = None,
        unit_id: Optional[int] = None,
        schedule_type: Optional[int] = None,
    ) -> Dict[str, Any]:
        """스케줄 목록 조회 (페이지네이션)"""
        # 기본 쿼리
        query = select(ArtistSchedule).options(
            selectinload(ArtistSchedule.members),
            selectinload(ArtistSchedule.contents),
        )

        # 필터 조건 추가
        conditions = []
        if artist_id is not None:
            conditions.append(ArtistSchedule.artist_id == artist_id)
        if unit_id is not None:
            conditions.append(ArtistSchedule.unit_id == unit_id)
        if schedule_type is not None:
            conditions.append(ArtistSchedule.type == schedule_type)

        if conditions:
            query = query.where(and_(*conditions))

        # 정렬 (최신순)
        query = query.order_by(desc(ArtistSchedule.start_time))

        # 전체 개수 조회
        count_query = select(func.count(ArtistSchedule.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_count = await self.db.scalar(count_query)

        # 페이지네이션
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        schedules = result.scalars().all()

        return {
            "items": schedules,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

    async def find_artist_by_ko_name(self, ko_name: str) -> Optional[Artist]:
        """한글명으로 아티스트 찾기"""
        query = (
            select(Artist)
            .join(ArtistName)
            .where(and_(ArtistName.code == "ko", ArtistName.name == ko_name))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_artist_by_member_ko_name(self, ko_name: str) -> Optional[Artist]:
        """멤버 한글명으로 아티스트 찾기"""
        query = (
            select(Artist)
            .join(ArtistName)
            .where(and_(ArtistName.code == "ko", ArtistName.name == ko_name))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def import_schedules_from_json(
        self, schedule_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """JSON 데이터에서 스케줄 가져오기"""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        unmatched_artists = set()

        for item in schedule_data:
            try:
                # artist_ko_name이 없으면 스킵
                if not item.get("artist_ko_name"):
                    skipped_count += 1
                    continue

                # 아티스트 찾기
                artist = await self.find_artist_by_ko_name(item["artist_ko_name"])
                if not artist:
                    unmatched_artists.add(item["artist_ko_name"])
                    skipped_count += 1
                    continue

                # 시간 변환 (ISO 8601 -> 밀리초)
                start_time = int(
                    datetime.fromisoformat(
                        item["schedule_start_time"].replace("Z", "+00:00")
                    ).timestamp()
                    * 1000
                )
                end_time = int(
                    datetime.fromisoformat(
                        item["schedule_end_time"].replace("Z", "+00:00")
                    ).timestamp()
                    * 1000
                )

                # 스케줄 생성 요청
                schedule_request = ArtistScheduleCreateRequest(
                    artist_id=artist.id,
                    unit_id=None,  # 필요시 추가 로직으로 설정
                    artist_ko_name=item["artist_ko_name"],
                    type=item["schedule_type"],  # ScheduleType 열거형 값으로 직접 사용
                    start_time=start_time,
                    end_time=end_time,
                    text=item.get("schedule_text"),
                    title=item["schedule_title"],
                    channel=item.get("schedule_channel"),
                    location=item.get("schedule_location"),
                    members=[],
                    contents=[],
                )

                # 멤버들 처리
                for member_data in item.get("schedule_members", []):
                    # 멤버 아티스트 찾기
                    member_artist = await self.find_artist_by_member_ko_name(
                        member_data["ko_name"]
                    )

                    member_request = ScheduleMemberCreateRequest(
                        ko_name=member_data["ko_name"],
                        en_name=member_data["en_name"],
                        artist_id=member_artist.id if member_artist else None,
                    )
                    schedule_request.members.append(member_request)

                # 콘텐츠들 처리
                for content_data in item.get("schedule_contents", []):
                    content_request = ScheduleContentCreateRequest(
                        type=content_data["schedule_content_type"],
                        path=content_data["schedule_content_path"],
                        title=content_data.get("schedule_content_title"),
                    )
                    schedule_request.contents.append(content_request)

                # 스케줄 생성
                await self.create_schedule(schedule_request)
                imported_count += 1

            except Exception as e:
                print(
                    f"Error importing schedule for {item.get('artist_ko_name', 'Unknown')}: {e}"
                )
                print(f"Item data: {item}")
                error_count += 1
                continue

        return {
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "error_count": error_count,
            "total_processed": len(schedule_data),
            "unmatched_artists": list(unmatched_artists)[:10],  # 처음 10개만 반환
            "unmatched_artists_count": len(unmatched_artists),
        }
