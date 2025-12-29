import sys
import traceback
from datetime import datetime
from pathlib import Path as PathLib
from typing import Any, Dict, List

# 프로젝트 루트를 Python path에 추가 (메인 API의 app 모듈 접근용)
project_root = PathLib(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.features.artists.models import Artist, ArtistName  # noqa: E402
from app.features.artists.models.artist_schedule import ArtistSchedule  # noqa: E402
from app.features.artists.schemas import (  # noqa: E402
    ArtistScheduleCreateRequest,
    ScheduleContentCreateRequest,
    ScheduleMemberCreateRequest,
)


class ArtistScheduleRepository:
    """스크래핑 서비스 전용 아티스트 스케줄 레포지토리"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_artist_by_ko_name(self, ko_name: str):
        """한글명으로 아티스트 찾기"""
        from sqlalchemy import and_, select

        query = (
            select(Artist)
            .join(ArtistName)
            .where(and_(ArtistName.code == "ko", ArtistName.name == ko_name))
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def find_artist_by_member_ko_name(self, ko_name: str):
        """멤버 한글명으로 아티스트 찾기"""
        from sqlalchemy import and_, select

        query = (
            select(Artist)
            .join(ArtistName)
            .where(and_(ArtistName.code == "ko", ArtistName.name == ko_name))
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def find_existing_schedule(self, artist_id: int, title: str, start_time: int):
        """중복 스케줄 찾기"""
        from sqlalchemy import and_, select

        query = select(ArtistSchedule).where(
            and_(
                ArtistSchedule.artist_id == artist_id,
                ArtistSchedule.title == title,
                ArtistSchedule.start_time == start_time,
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create_schedule(self, request: ArtistScheduleCreateRequest):
        """스케줄 생성"""
        from app.features.artists.models.schedule_content import ScheduleContent
        from app.features.artists.models.schedule_member import ScheduleMember

        schedule = ArtistSchedule(
            artist_id=request.artist_id,
            unit_id=request.unit_id,
            artist_ko_name=request.artist_ko_name,
            type=request.type.value,
            start_time=request.start_time,
            end_time=request.end_time,
            text=request.text,
            title=request.title,
            channel=request.channel,
            location=request.location,
        )

        self._session.add(schedule)
        await self._session.flush()

        # 멤버들 생성
        for member_req in request.members:
            member = ScheduleMember(
                schedule_id=schedule.id,
                artist_id=member_req.artist_id,
                ko_name=member_req.ko_name,
                en_name=member_req.en_name,
            )
            self._session.add(member)

        # 콘텐츠들 생성
        for content_req in request.contents:
            content = ScheduleContent(
                schedule_id=schedule.id,
                type=content_req.type,
                path=content_req.path,
                title=content_req.title,
            )
            self._session.add(content)

        await self._session.commit()
        await self._session.refresh(schedule)

        return schedule

    async def update_existing_schedule(
        self, schedule_id: int, request: ArtistScheduleCreateRequest
    ):
        """기존 스케줄 업데이트"""
        from sqlalchemy import select

        from app.features.artists.models.schedule_content import ScheduleContent
        from app.features.artists.models.schedule_member import ScheduleMember

        # 스케줄 조회
        query = select(ArtistSchedule).where(ArtistSchedule.id == schedule_id)
        result = await self._session.execute(query)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return None

        # 스케줄 필드 업데이트
        setattr(schedule, "artist_id", request.artist_id)
        setattr(schedule, "unit_id", request.unit_id)
        setattr(schedule, "artist_ko_name", request.artist_ko_name)
        setattr(schedule, "type", request.type.value)
        setattr(schedule, "start_time", request.start_time)
        setattr(schedule, "end_time", request.end_time)
        setattr(schedule, "text", request.text)
        setattr(schedule, "title", request.title)
        setattr(schedule, "channel", request.channel)
        setattr(schedule, "location", request.location)

        # 기존 멤버 및 콘텐츠 삭제
        await self._session.execute(
            ScheduleMember.__table__.delete().where(
                ScheduleMember.schedule_id == schedule_id
            )
        )
        await self._session.execute(
            ScheduleContent.__table__.delete().where(
                ScheduleContent.schedule_id == schedule_id
            )
        )

        # 새 멤버들 생성
        for member_req in request.members:
            member = ScheduleMember(
                schedule_id=schedule.id,
                artist_id=member_req.artist_id,
                ko_name=member_req.ko_name,
                en_name=member_req.en_name,
            )
            self._session.add(member)

        # 새 콘텐츠들 생성
        for content_req in request.contents:
            content = ScheduleContent(
                schedule_id=schedule.id,
                type=content_req.type,
                path=content_req.path,
                title=content_req.title,
            )
            self._session.add(content)

        await self._session.commit()
        await self._session.refresh(schedule)

        return schedule

    async def import_schedules_from_json(
        self, schedule_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """JSON 데이터에서 스케줄 가져오기"""
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        unmatched_artists = set()

        for i, item in enumerate(schedule_data):
            try:
                # 진행 상황 로깅 (100개마다)
                if i % 100 == 0:
                    print(
                        f"Processing item {i + 1}/{len(schedule_data)}: {item.get('artist_ko_name', 'Unknown')}"
                    )

                # artist_ko_name이 없으면 스킵
                if not item.get("artist_ko_name"):
                    skipped_count += 1
                    continue

                # 아티스트 찾기
                print(f"Looking for artist: {item['artist_ko_name']}")
                artist = await self.find_artist_by_ko_name(item["artist_ko_name"])
                print(f"Found artist: {artist}")
                if not artist:
                    print(f"Artist not found: {item['artist_ko_name']}")
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
                artist_id = getattr(artist, "id", None)
                if artist_id is None:
                    continue

                schedule_request = ArtistScheduleCreateRequest(
                    artist_id=artist_id,
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

                    member_artist_id = (
                        getattr(member_artist, "id", None) if member_artist else None
                    )
                    member_request = ScheduleMemberCreateRequest(
                        ko_name=member_data["ko_name"],
                        en_name=member_data["en_name"],
                        artist_id=member_artist_id,
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

                # 중복 스케줄 체크
                existing_schedule = await self.find_existing_schedule(
                    artist_id, schedule_request.title, schedule_request.start_time
                )

                if existing_schedule:
                    # 기존 스케줄 업데이트
                    existing_schedule_id = getattr(existing_schedule, "id", None)
                    if existing_schedule_id is not None:
                        await self.update_existing_schedule(
                            existing_schedule_id, schedule_request
                        )
                    updated_count += 1
                    print(f"Updated schedule: {schedule_request.title}")
                else:
                    # 새 스케줄 생성
                    await self.create_schedule(schedule_request)
                    imported_count += 1
                    print(f"Created new schedule: {schedule_request.title}")

            except Exception as e:
                print(
                    f"Error importing schedule for {item.get('artist_ko_name', 'Unknown')}: {e}"
                )
                print(f"Item data: {item}")
                print(f"Full traceback: {traceback.format_exc()}")
                error_count += 1
                continue

        return {
            "imported_count": imported_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "error_count": error_count,
            "total_processed": len(schedule_data),
            "unmatched_artists": list(unmatched_artists)[:10],  # 처음 10개만 반환
            "unmatched_artists_count": len(unmatched_artists),
        }
