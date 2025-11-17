from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, case
from sqlalchemy.orm import selectinload
from app.models.pod import Pod, PodMember
from app.models.pod.pod_rating import PodRating
from app.models.pod.pod_view import PodView
from app.models.pod.pod_like import PodLike
from app.models.pod.pod_status import PodStatus
from app.models.user import User
from app.schemas.pod_review import SimplePodDto
from app.models.pod.pod_enums import get_subcategories_by_main_category
from datetime import date, time, datetime, timedelta, timezone
import json


class PodCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: 파티 생성
    async def create_pod(
        self,
        owner_id: int,
        title: str,
        description: Optional[str],
        image_url: Optional[str],
        thumbnail_url: Optional[str],
        sub_categories: List[str],
        capacity: int,
        place: str,
        address: str,
        sub_address: Optional[str],
        meeting_date: date,
        meeting_time: time,
        selected_artist_id: Optional[int] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        status: PodStatus = PodStatus.RECRUITING,
    ) -> Pod:
        # description이 없으면 빈 문자열로 설정
        if not description:
            description = ""

        pod = Pod(
            owner_id=owner_id,
            selected_artist_id=selected_artist_id,
            title=title,
            description=description,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            sub_categories=(
                json.dumps(sub_categories, ensure_ascii=False)
                if sub_categories
                else None
            ),
            capacity=capacity,
            place=place,
            address=address,
            sub_address=sub_address,
            x=x,
            y=y,
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            status=status,
        )
        self.db.add(pod)
        await self.db.flush()
        return pod

    # - MARK: 파티 생성 (채팅방 포함)
    async def create_pod_with_chat(
        self,
        owner_id: int,
        title: str,
        description: Optional[str],
        image_url: Optional[str],
        thumbnail_url: Optional[str],
        sub_categories: List[str],
        capacity: int,
        place: str,
        address: str,
        sub_address: Optional[str],
        meeting_date: date,
        meeting_time: time,
        selected_artist_id: Optional[int] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        status: PodStatus = PodStatus.RECRUITING,
    ) -> Pod:
        """파티 생성 후 Sendbird 채팅방도 함께 생성"""
        from app.services.sendbird_service import SendbirdService
        from datetime import datetime

        # 파티 생성
        pod = await self.create_pod(
            owner_id=owner_id,
            title=title,
            description=description,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            sub_categories=sub_categories,
            capacity=capacity,
            place=place,
            address=address,
            sub_address=sub_address,
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            selected_artist_id=selected_artist_id,
            x=x,
            y=y,
            status=status,
        )

        try:
            # Sendbird 채팅방 생성
            sendbird_service = SendbirdService()
            channel_url = f"pod_{pod.id}_{int(datetime.now().timestamp())}"

            # SimplePodDto 객체 생성 (meeting_date와 meeting_time을 하나로 합쳐서 timestamp로 변환)
            def _convert_to_combined_timestamp(meeting_date, meeting_time):
                """date와 time 객체를 UTC로 해석하여 하나의 timestamp로 변환"""
                if meeting_date is None:
                    return None
                if meeting_time is None:
                    # time이 없으면 date만 사용 (00:00:00)
                    dt = datetime.combine(meeting_date, time.min, tzinfo=timezone.utc)
                else:
                    # date와 time을 결합 (UTC로 해석)
                    dt = datetime.combine(
                        meeting_date, meeting_time, tzinfo=timezone.utc
                    )
                return int(dt.timestamp() * 1000)  # milliseconds

            simple_pod_dto = SimplePodDto(
                id=pod.id,
                owner_id=owner_id,
                title=title,
                thumbnail_url=thumbnail_url or image_url or "",
                sub_categories=sub_categories,
                meeting_place=place,
                meeting_date=_convert_to_combined_timestamp(meeting_date, meeting_time),
            )

            # 채팅방 생성 (파티장만 참여)
            channel_data = await sendbird_service.create_group_channel_with_join(
                user_ids=[owner_id],
                name=title,
                channel_url=channel_url,
                cover_url=thumbnail_url
                or image_url,  # 채팅방 커버 이미지로 썸네일 우선 사용
                data=simple_pod_dto.model_dump(mode="json", by_alias=True),
            )

            if channel_data and "channel_url" in channel_data:
                # 생성된 채팅방 URL을 파티에 저장
                pod.chat_channel_url = channel_data["channel_url"]
                await self.db.commit()
                print(f"파티 {pod.id} 채팅방 생성 성공: {channel_data['channel_url']}")
            else:
                print(f"파티 {pod.id} 채팅방 생성 실패")
                await self.db.rollback()

        except Exception as e:
            print(f"Sendbird 설정 오류: {e}")
            await self.db.rollback()
            raise e

        return pod

    async def get_pods_with_chat_channels(self) -> List[Pod]:
        """채팅방 URL이 있는 모든 파티 조회"""
        result = await self.db.execute(
            select(Pod).where(
                and_(
                    Pod.chat_channel_url.isnot(None),
                    Pod.is_active == True,
                )
            )
        )
        return list(result.scalars().all())

    # - MARK: 파티 조회
    async def get_pod_by_id(self, pod_id: int) -> Optional[Pod]:
        result = await self.db.execute(
            select(Pod)
            .options(selectinload(Pod.images))
            .where(Pod.id == pod_id, Pod.is_active == True)
        )
        return result.scalar_one_or_none()

    # - MARK: 파티 수정
    async def update_pod(self, pod_id: int, **fields) -> Optional[Pod]:
        pod = await self.get_pod_by_id(pod_id)
        if not pod:
            return None

        for field, value in fields.items():
            if hasattr(pod, field):
                setattr(pod, field, value)

        await self.db.commit()
        await self.db.refresh(pod)
        return pod

    # - MARK: 파티 삭제
    async def delete_pod(self, pod_id: int) -> None:
        pod = await self.get_pod_by_id(pod_id)
        if pod:
            pod.is_active = False
            await self.db.commit()

    # - MARK: 파티 목록 조회
    async def get_pods(
        self,
        user_id: Optional[int] = None,
        selected_artist_id: Optional[int] = None,
        main_category: Optional[str] = None,
        sub_categories: Optional[List[str]] = None,
        location: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        size: int = 20,
    ) -> Dict[str, Any]:
        """파티 목록 조회 (검색 조건 포함)"""
        offset = (page - 1) * size

        # 기본 쿼리
        query = (
            select(Pod).options(selectinload(Pod.images)).where(Pod.is_active == True)
        )

        # 조건 추가
        if selected_artist_id:
            query = query.where(Pod.selected_artist_id == selected_artist_id)

        if start_date:
            query = query.where(Pod.meeting_date >= start_date)

        if end_date:
            query = query.where(Pod.meeting_date <= end_date)

        if location:
            query = query.where(
                or_(
                    Pod.place.contains(location),
                    Pod.address.contains(location),
                )
            )

        if sub_categories:
            # JSON 배열에서 서브 카테고리 검색
            category_conditions = []
            for category in sub_categories:
                category_conditions.append(Pod.sub_categories.contains(category))
            query = query.where(or_(*category_conditions))

        # 차단된 유저가 만든 파티 제외
        if user_id:
            from app.models.user_block import UserBlock

            blocked_query = select(UserBlock.blocked_id).where(
                UserBlock.blocker_id == user_id
            )
            query = query.where(~Pod.owner_id.in_(blocked_query))

        # 정렬 (최신순)
        query = query.order_by(desc(Pod.created_at))

        # 전체 개수 조회
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # 페이지네이션 적용
        query = query.offset(offset).limit(size)

        # 실행
        result = await self.db.execute(query)
        pods = result.scalars().all()

        return {
            "items": pods,
            "total_count": total_count,
            "page": page,
            "page_size": size,
            "total_pages": (total_count + size - 1) // size,
        }

    # - MARK: 요즘 인기 있는 파티 조회
    async def get_trending_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        page: int = 1,
        size: int = 20,
    ) -> List[Pod]:
        """
        요즘 인기 있는 파티 조회
        조건:
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 최근 7일간 생성된 파티
        정렬 우선순위:
        1. 조회수 높은 순
        2. 좋아요 수 높은 순
        3. 최신순
        """
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        # 차단된 유저가 만든 파티 제외 조건
        from app.models.user_block import UserBlock

        blocked_query = select(UserBlock.blocked_id).where(
            UserBlock.blocker_id == user_id
        )

        # 기본 조건: 마감되지 않은 파티 + 선택된 아티스트 기준 + 최근 7일간 생성
        base_conditions = and_(
            Pod.is_active == True,
            Pod.status == PodStatus.RECRUITING,  # 모집중인 파티만
            Pod.meeting_date >= now.date(),  # 마감되지 않은 파티
            Pod.selected_artist_id == selected_artist_id,  # 선택된 아티스트 기준
            Pod.created_at >= seven_days_ago,  # 최근 7일간 생성
            Pod.owner_id != user_id,  # 본인이 개설한 파티 제외
            ~Pod.owner_id.in_(blocked_query),  # 차단된 유저가 만든 파티 제외
        )

        # 조회수와 좋아요 수를 서브쿼리로 조회
        view_count_subquery = (
            select(func.count(PodView.id))
            .where(PodView.pod_id == Pod.id)
            .scalar_subquery()
        )

        like_count_subquery = (
            select(func.count())
            .select_from(PodLike)
            .where(PodLike.pod_id == Pod.id)
            .scalar_subquery()
        )

        # 메인 쿼리
        trending_query = (
            select(
                Pod,
                view_count_subquery.label("view_count"),
                like_count_subquery.label("like_count"),
            )
            .options(selectinload(Pod.images))
            .where(base_conditions)
            .order_by(
                desc(view_count_subquery),  # 조회수 높은 순
                desc(like_count_subquery),  # 좋아요 수 높은 순
                desc(Pod.created_at),  # 최신순
            )
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.db.execute(trending_query)
        trending_pods = result.scalars().all()

        return trending_pods

    # - MARK: 마감 임박 파티 조회
    async def get_closing_soon_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> List[Pod]:
        """
        마감 임박 파티 조회
        조건:
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 24시간 이내 시작하는 파티
        정렬 우선순위:
        1. 시작 시간이 가까운 순
        2. 조회수 높은 순
        """
        now = datetime.now(timezone.utc)
        twenty_four_hours_later = now + timedelta(hours=24)

        # 차단된 유저가 만든 파티 제외 조건
        from app.models.user_block import UserBlock

        blocked_query = select(UserBlock.blocked_id).where(
            UserBlock.blocker_id == user_id
        )

        # 기본 조건: 마감되지 않은 파티 + 선택된 아티스트 기준
        base_conditions = and_(
            Pod.is_active == True,
            Pod.status == PodStatus.RECRUITING,  # 모집중인 파티만
            Pod.meeting_date >= now.date(),  # 마감되지 않은 파티
            Pod.selected_artist_id == selected_artist_id,  # 선택된 아티스트 기준
            Pod.owner_id != user_id,  # 본인이 개설한 파티 제외
            ~Pod.owner_id.in_(blocked_query),  # 차단된 유저가 만든 파티 제외
        )

        # 24시간 이내 시작하는 파티 조건
        time_condition = and_(
            Pod.meeting_date == now.date(),  # 오늘 시작하는 파티
            Pod.meeting_time >= now.time(),  # 현재 시간 이후
            Pod.meeting_time <= twenty_four_hours_later.time(),  # 24시간 이내
        )

        # 조회수 서브쿼리
        view_count_subquery = (
            select(func.count(PodView.id))
            .where(PodView.pod_id == Pod.id)
            .scalar_subquery()
        )

        # 메인 쿼리
        offset = (page - 1) * size
        closing_soon_query = (
            select(Pod, view_count_subquery.label("view_count"))
            .options(selectinload(Pod.images))
            .where(and_(base_conditions, time_condition))
            .order_by(
                Pod.meeting_time.asc(),  # 시작 시간이 가까운 순
                desc(view_count_subquery),  # 조회수 높은 순
            )
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(closing_soon_query)
        closing_soon_pods = result.scalars().all()

        return closing_soon_pods

    # - MARK: 우리 만난적 있어요 파티 조회
    async def get_history_based_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        page: int = 1,
        size: int = 20,
    ) -> List[Pod]:
        """
        우리 만난적 있어요 파티 조회
        조건:
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        정렬 우선순위:
        1. 참여한 팟(평점 4점 이상, 90일 이내)의 개설자가 개설한 팟
           - 가장 최근에 참여한 5개의 팟의 카테고리와 동일한 카테고리 우선
           - 가장 최근에 참여한 5개의 팟의 동일한 지역의 모임 우선
        2. 유저가 개설한 팟에 참여한 유저(90일 이내)가 개설한 모임
           - 가장 최근에 참여한 5개의 팟의 카테고리와 동일한 카테고리 우선
           - 가장 최근에 참여한 5개의 팟의 동일한 지역의 모임 우선
        """
        now = datetime.now(timezone.utc)
        ninety_days_ago = now - timedelta(days=90)

        # 차단된 유저가 만든 파티 제외 조건
        from app.models.user_block import UserBlock

        blocked_query = select(UserBlock.blocked_id).where(
            UserBlock.blocker_id == user_id
        )

        # 기본 조건: 마감되지 않은 파티 + 선택된 아티스트 기준
        base_conditions = and_(
            Pod.is_active == True,
            Pod.status == PodStatus.RECRUITING,  # 모집중인 파티만
            Pod.meeting_date >= now.date(),  # 마감되지 않은 파티
            Pod.selected_artist_id == selected_artist_id,  # 선택된 아티스트 기준
            Pod.owner_id != user_id,  # 본인이 개설한 파티 제외
            ~Pod.owner_id.in_(blocked_query),  # 차단된 유저가 만든 파티 제외
        )

        # 1순위: 참여한 팟(평점 4점 이상, 90일 이내)의 개설자가 개설한 팟
        # 사용자가 참여한 파티 조회 (PodMember + PodRating 테이블 사용)
        ninety_days_ago_timestamp = int(ninety_days_ago.timestamp())

        participated_pods_query = (
            select(Pod.id, Pod.sub_categories, Pod.place)
            .join(PodMember, Pod.id == PodMember.pod_id)
            .join(PodRating, Pod.id == PodRating.pod_id)
            .where(
                and_(
                    PodMember.user_id == user_id,
                    PodRating.user_id == user_id,
                    PodRating.rating >= 4.0,
                    PodRating.created_at >= ninety_days_ago,
                )
            )
            .order_by(desc(PodRating.created_at))
            .limit(5)
        )

        participated_result = await self.db.execute(participated_pods_query)
        participated_pods = participated_result.all()

        # 2순위: 유저가 개설한 팟에 참여한 유저가 개설한 모임
        # 사용자가 개설한 파티에 참여한 유저들 조회
        my_pods_query = select(Pod.id).where(
            and_(
                Pod.owner_id == user_id,
                Pod.created_at >= ninety_days_ago,
            )
        )
        my_pods_result = await self.db.execute(my_pods_query)
        my_pod_ids = [row[0] for row in my_pods_result.all()]

        if my_pod_ids:
            # 내 파티에 참여한 유저들 조회
            participants_query = (
                select(PodMember.user_id)
                .where(PodMember.pod_id.in_(my_pod_ids))
                .distinct()
            )
            participants_result = await self.db.execute(participants_query)
            participant_ids = [row[0] for row in participants_result.all()]

            # 참여자들이 개설한 파티 조회
            participant_pods_query = (
                select(Pod.id, Pod.sub_categories, Pod.place)
                .where(
                    and_(
                        Pod.owner_id.in_(participant_ids),
                        Pod.created_at >= ninety_days_ago,
                    )
                )
                .order_by(desc(Pod.created_at))
                .limit(5)
            )
            participant_result = await self.db.execute(participant_pods_query)
            participant_pods = participant_result.all()
        else:
            participant_pods = []

        # 모든 히스토리 기반 파티 ID 수집
        history_pod_ids = set()
        preferred_categories = set()
        preferred_locations = set()

        for pod_data in participated_pods + participant_pods:
            history_pod_ids.add(pod_data[0])
            if pod_data[1]:  # sub_categories
                try:
                    categories = (
                        json.loads(pod_data[1])
                        if isinstance(pod_data[1], str)
                        else pod_data[1]
                    )
                    preferred_categories.update(categories)
                except:
                    pass
            if pod_data[2]:  # place
                preferred_locations.add(pod_data[2])

        # 히스토리 기반 파티 조회 쿼리
        history_conditions = base_conditions
        if history_pod_ids:
            history_conditions = and_(
                history_conditions,
                Pod.owner_id.in_(
                    select(Pod.owner_id).where(Pod.id.in_(history_pod_ids))
                ),
            )

        # 선호 카테고리와 지역 우선순위 적용
        order_conditions = []

        if preferred_categories:
            category_priority = case(
                *[
                    (Pod.sub_categories.contains(cat), 1)
                    for cat in preferred_categories
                ],
                else_=2,
            )
            order_conditions.append(category_priority)

        if preferred_locations:
            location_priority = case(
                *[(Pod.place == loc, 1) for loc in preferred_locations], else_=2
            )
            order_conditions.append(location_priority)

        # 기본 정렬 (최신순)
        order_conditions.append(desc(Pod.created_at))

        # 메인 쿼리
        offset = (page - 1) * size
        history_query = (
            select(Pod)
            .options(selectinload(Pod.images))
            .where(history_conditions)
            .order_by(*order_conditions)
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(history_query)
        history_pods = result.scalars().all()

        return history_pods

    # - MARK: 인기 카테고리 파티 조회
    async def get_popular_categories_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> List[Pod]:
        """
        인기 카테고리 파티 조회
        조건:
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 최근 일주일 기준 가장 많이 개설된 카테고리 && 최근 일주일 기준 가장 조회가 많은 카테고리
        정렬 우선순위:
        1. 에디터가 설정한 지역의 모임 우선 (선택사항)
        2. 조회수 높은 순
        """
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        # 기본 조건: 마감되지 않은 파티 + 선택된 아티스트 기준
        base_conditions = and_(
            Pod.is_active == True,
            Pod.status == PodStatus.RECRUITING,  # 모집중인 파티만
            Pod.meeting_date >= now.date(),  # 마감되지 않은 파티
            Pod.selected_artist_id == selected_artist_id,  # 선택된 아티스트 기준
            Pod.owner_id != user_id,  # 본인이 개설한 파티 제외
        )

        # 최근 일주일간 가장 많이 개설된 카테고리 조회
        popular_categories_query = (
            select(Pod.sub_categories, func.count().label("category_count"))
            .where(
                and_(
                    Pod.is_active == True,
                    Pod.selected_artist_id == selected_artist_id,
                    Pod.created_at >= seven_days_ago,
                )
            )
            .group_by(Pod.sub_categories)
            .order_by(desc("category_count"))
            .limit(3)
        )

        popular_result = await self.db.execute(popular_categories_query)
        popular_categories = [row[0] for row in popular_result.all()]

        # 최근 일주일간 가장 조회가 많은 카테고리 조회
        viewed_categories_query = (
            select(Pod.sub_categories, func.count(PodView.id).label("view_count"))
            .join(PodView, Pod.id == PodView.pod_id)
            .where(
                and_(
                    Pod.is_active == True,
                    Pod.selected_artist_id == selected_artist_id,
                    Pod.created_at >= seven_days_ago,
                    PodView.created_at >= seven_days_ago,
                )
            )
            .group_by(Pod.sub_categories)
            .order_by(desc("view_count"))
            .limit(3)
        )

        viewed_result = await self.db.execute(viewed_categories_query)
        viewed_categories = [row[0] for row in viewed_result.all()]

        # 인기 카테고리 통합
        all_popular_categories = set(popular_categories + viewed_categories)

        # 조회수 서브쿼리
        view_count_subquery = (
            select(func.count(PodView.id))
            .where(PodView.pod_id == Pod.id)
            .scalar_subquery()
        )

        # 카테고리 조건
        category_conditions = base_conditions
        if all_popular_categories:
            category_priority = case(
                *[(Pod.sub_categories == cat, 1) for cat in all_popular_categories],
                else_=2,
            )
        else:
            # 인기 카테고리가 없으면 조회수로만 정렬
            category_priority = None

        # 지역 조건
        location_conditions = []
        if location:
            location_conditions.append(Pod.place.contains(location))

        # 메인 쿼리
        offset = (page - 1) * size
        # 정렬 조건 설정
        order_conditions = []
        if category_priority is not None:
            order_conditions.append(category_priority)  # 인기 카테고리 우선
        order_conditions.append(desc(view_count_subquery))  # 조회수 높은 순
        order_conditions.append(desc(Pod.created_at))  # 최신순

        popular_query = (
            select(Pod, view_count_subquery.label("view_count"))
            .options(selectinload(Pod.images))
            .where(category_conditions)
            .order_by(*order_conditions)
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(popular_query)
        popular_pods = result.scalars().all()

        return popular_pods

    # - MARK: 조회수 증가 (공통 메서드)
    async def _increment_view_count(
        self, pod_id: int, user_id: Optional[int] = None
    ) -> None:
        """조회수 증가 (중복 방지)"""
        if not user_id:
            return

        # 파티 정보 조회
        pod = await self.get_pod_by_id(pod_id)
        if not pod or user_id == pod.owner_id:
            return  # 파티가 없거나 본인 파티면 카운트하지 않음

        # 중복 조회 방지 (하루에 한 번만)
        existing_view = await self.db.execute(
            select(PodView).where(
                PodView.pod_id == pod_id,
                PodView.user_id == user_id,
                PodView.created_at >= datetime.now().date(),
            )
        )
        if not existing_view.scalar_one_or_none():
            view = PodView(pod_id=pod_id, user_id=user_id)
            self.db.add(view)
            await self.db.commit()

            # 조회수 달성 알림 체크
            await self._check_views_threshold(pod_id)

    # - MARK: 파티 상세 조회
    async def get_pod_detail(
        self, pod_id: int, user_id: Optional[int] = None
    ) -> Optional[Pod]:
        """파티 상세 정보 조회"""
        query = (
            select(Pod)
            .options(selectinload(Pod.images))
            .where(Pod.id == pod_id, Pod.is_active == True)
        )

        result = await self.db.execute(query)
        pod = result.scalar_one_or_none()

        if not pod:
            return None

        # 조회수 증가
        await self._increment_view_count(pod_id, user_id)

        return pod

    # - MARK: 파티 상태 업데이트
    async def update_pod_status(self, pod_id: int, status: PodStatus) -> bool:
        """파티 상태 업데이트"""
        pod = await self.get_pod_by_id(pod_id)
        if not pod:
            return False

        pod.status = status
        await self.db.commit()
        return True

    # - MARK: 파티 검색
    async def search_pods(
        self,
        query: str,
        selected_artist_id: Optional[int] = None,
        main_category: Optional[str] = None,
        sub_categories: Optional[List[str]] = None,
        location: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        size: int = 20,
    ) -> Dict[str, Any]:
        """파티 검색"""
        offset = (page - 1) * size

        # 기본 쿼리
        # query가 비어있으면 검색 조건 없이 is_active만 체크
        if query and query.strip():
            search_query = (
                select(Pod)
                .options(selectinload(Pod.images))
                .where(
                    and_(
                        Pod.is_active == True,
                        or_(
                            Pod.title.contains(query),
                            Pod.description.contains(query),
                            Pod.place.contains(query),
                        ),
                    )
                )
            )
        else:
            # query가 비어있으면 is_active만 체크
            search_query = (
                select(Pod)
                .options(selectinload(Pod.images))
                .where(Pod.is_active == True)
            )

        # 조건 추가
        if selected_artist_id:
            search_query = search_query.where(
                Pod.selected_artist_id == selected_artist_id
            )

        if start_date:
            search_query = search_query.where(Pod.meeting_date >= start_date)

        if end_date:
            search_query = search_query.where(Pod.meeting_date <= end_date)

        if location:
            search_query = search_query.where(
                or_(
                    Pod.place.contains(location),
                    Pod.address.contains(location),
                )
            )

        # main_category가 있으면 해당 메인 카테고리의 서브 카테고리들로 필터링
        if main_category:
            main_category_subcategories = get_subcategories_by_main_category(
                main_category
            )
            if main_category_subcategories:
                main_category_conditions = []
                for sub_cat in main_category_subcategories:
                    main_category_conditions.append(
                        Pod.sub_categories.contains(sub_cat)
                    )
                search_query = search_query.where(or_(*main_category_conditions))

        if sub_categories:
            category_conditions = []
            for category in sub_categories:
                category_conditions.append(Pod.sub_categories.contains(category))
            search_query = search_query.where(or_(*category_conditions))

        # 정렬 (최신순)
        search_query = search_query.order_by(desc(Pod.created_at))

        # 전체 개수 조회
        count_query = select(func.count()).select_from(search_query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # 페이지네이션 적용
        search_query = search_query.offset(offset).limit(size)

        # 실행
        result = await self.db.execute(search_query)
        pods = result.scalars().all()

        return {
            "items": pods,
            "total_count": total_count,
            "page": page,
            "page_size": size,
            "total_pages": (total_count + size - 1) // size,
        }

    # - MARK: 파티 참여자 조회
    async def get_pod_participants(self, pod_id: int) -> List[User]:
        """파티 참여자 목록 조회 (파티장 포함)"""
        query = (
            select(User)
            .join(PodMember, User.id == PodMember.user_id)
            .where(PodMember.pod_id == pod_id)
            .distinct()
        )

        result = await self.db.execute(query)
        participants = result.scalars().all()

        # 파티장도 포함시키기 위해 추가 조회
        pod_query = (
            select(Pod)
            .options(selectinload(Pod.images))
            .where(Pod.id == pod_id, Pod.is_active == True)
        )
        pod_result = await self.db.execute(pod_query)
        pod = pod_result.scalar_one_or_none()

        if pod:
            owner_query = select(User).where(User.id == pod.owner_id)
            owner_result = await self.db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            # 파티장이 참여자 목록에 없으면 추가
            if owner and owner not in participants:
                participants.append(owner)

        return participants

    # - MARK: 조회수 달성 알림 체크
    async def _check_views_threshold(self, pod_id: int) -> None:
        """조회수 10회 달성 시 파티장에게 알림 전송"""
        try:
            from app.services.fcm_service import FCMService
            from app.models.pod.pod_view import PodView

            # 현재 조회수 확인
            view_count_query = select(func.count(PodView.id)).where(
                PodView.pod_id == pod_id
            )
            view_count_result = await self.db.execute(view_count_query)
            view_count = view_count_result.scalar() or 0

            # 10회 달성 시에만 알림 전송
            if view_count == 10:
                # 파티 정보 조회
                pod = await self.get_pod_by_id(pod_id)
                if not pod:
                    return

                # 파티장 정보 조회
                owner_query = select(User).where(User.id == pod.owner_id)
                owner_result = await self.db.execute(owner_query)
                owner = owner_result.scalar_one_or_none()

                if owner and owner.fcm_token:
                    # FCM 서비스 초기화
                    fcm_service = FCMService()

                    # 조회수 달성 알림 전송
                    await fcm_service.send_pod_views_threshold(
                        token=owner.fcm_token,
                        party_name=pod.title,
                        pod_id=pod_id,
                        db=self.db,
                        user_id=owner.id,
                        related_user_id=pod.owner_id,
                    )
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"조회수 10회 달성 알림 전송 성공: pod_id={pod_id}, owner_id={owner.id}"
                    )
                else:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"파티장 FCM 토큰이 없음: pod_id={pod_id}, owner_id={pod.owner_id}"
                    )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"조회수 달성 알림 체크 실패: pod_id={pod_id}, error={e}")

    # - MARK: 파티 통계 조회
    async def get_joined_users_count(self, pod_id: int) -> int:
        """파티 참여자 수 조회"""
        query = select(func.count(PodMember.id)).where(PodMember.pod_id == pod_id)
        result = await self.db.execute(query)
        count = result.scalar() or 0
        return count + 1  # 파티장 포함

    async def get_like_count(self, pod_id: int) -> int:
        """파티 좋아요 수 조회"""
        query = select(func.count(PodLike.id)).where(PodLike.pod_id == pod_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_view_count(self, pod_id: int) -> int:
        """파티 조회수 조회"""
        query = select(func.count(PodView.id)).where(PodView.pod_id == pod_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def is_liked_by_user(self, pod_id: int, user_id: int) -> bool:
        """사용자가 파티를 좋아요했는지 확인"""
        query = select(PodLike.id).where(
            PodLike.pod_id == pod_id, PodLike.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_user_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """사용자가 생성한 파티 목록 조회"""
        offset = (page - 1) * size

        # 기본 쿼리
        query = (
            select(Pod)
            .options(selectinload(Pod.images))
            .where(
                and_(
                    Pod.is_active == True,
                    Pod.owner_id == user_id,
                )
            )
        )

        # 정렬 (최신순)
        query = query.order_by(desc(Pod.created_at))

        # 전체 개수 조회
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # 페이지네이션 적용
        query = query.offset(offset).limit(size)

        # 실행
        result = await self.db.execute(query)
        pods = result.scalars().all()

        return {
            "items": pods,
            "total_count": total_count,
            "page": page,
            "page_size": size,
            "total_pages": (total_count + size - 1) // size,
        }

    async def get_user_joined_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """사용자가 참여한 파티 목록 조회"""
        offset = (page - 1) * size

        # 기본 쿼리 (PodMember를 통해 참여한 파티 조회)
        query = (
            select(Pod)
            .options(selectinload(Pod.images))
            .join(PodMember, Pod.id == PodMember.pod_id)
            .where(
                and_(
                    Pod.is_active == True,
                    PodMember.user_id == user_id,
                )
            )
        )

        # 정렬 (최신순)
        query = query.order_by(desc(Pod.created_at))

        # 전체 개수 조회
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # 페이지네이션 적용
        query = query.offset(offset).limit(size)

        # 실행
        result = await self.db.execute(query)
        pods = result.scalars().all()

        return {
            "items": pods,
            "total_count": total_count,
            "page": page,
            "page_size": size,
            "total_pages": (total_count + size - 1) // size,
        }

    async def get_user_liked_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """사용자가 좋아요한 파티 목록 조회"""
        offset = (page - 1) * size

        # 기본 쿼리 (PodLike를 통해 좋아요한 파티 조회)
        query = (
            select(Pod)
            .options(selectinload(Pod.images))
            .join(PodLike, Pod.id == PodLike.pod_id)
            .where(
                and_(
                    Pod.is_active == True,
                    PodLike.user_id == user_id,
                )
            )
        )

        # 정렬 (최신순)
        query = query.order_by(desc(Pod.created_at))

        # 전체 개수 조회
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        # 페이지네이션 적용
        query = query.offset(offset).limit(size)

        # 실행
        result = await self.db.execute(query)
        pods = result.scalars().all()

        return {
            "items": pods,
            "total_count": total_count,
            "page": page,
            "page_size": size,
            "total_pages": (total_count + size - 1) // size,
        }

    # - MARK: 파티 멤버 관련
    async def get_pod_members(self, pod_id: int) -> List[PodMember]:
        """파티의 모든 멤버 조회"""
        query = select(PodMember).where(PodMember.pod_id == pod_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def is_pod_member(self, pod_id: int, user_id: int) -> bool:
        """사용자가 파티 멤버인지 확인"""
        query = select(PodMember).where(
            and_(PodMember.pod_id == pod_id, PodMember.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def remove_pod_member(self, pod_id: int, user_id: int) -> bool:
        """파티에서 멤버 제거"""
        query = select(PodMember).where(
            and_(PodMember.pod_id == pod_id, PodMember.user_id == user_id)
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if member:
            await self.db.delete(member)
            await self.db.commit()
            return True
        return False
