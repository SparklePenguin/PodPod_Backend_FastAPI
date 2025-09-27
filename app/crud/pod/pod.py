from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, case
from app.models.pod import Pod, PodMember
from app.models.pod.pod_rating import PodRating
from app.models.pod.pod_view import PodView
from app.models.pod.pod_status import PodStatus
from app.models.user import User
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
        status: PodStatus = PodStatus.RECRUITING,
    ) -> Pod:
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
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            status=status,
        )
        self.db.add(pod)
        await self.db.flush()

        # owner를 멤버로 포함 (role=owner)
        self.db.add(PodMember(pod_id=pod.id, user_id=owner_id, role="owner"))

        await self.db.commit()
        await self.db.refresh(pod)
        return pod

    # - MARK: 파티 조회
    async def get_pod_by_id(self, pod_id: int) -> Optional[Pod]:
        result = await self.db.execute(select(Pod).where(Pod.id == pod_id))
        return result.scalar_one_or_none()

    # - MARK: 파티 수정
    async def update_pod(
        self,
        pod_id: int,
        **fields,
    ) -> Optional[Pod]:
        pod = await self.get_pod_by_id(pod_id)
        if pod is None:
            return None

        for key, value in fields.items():
            if value is not None and hasattr(pod, key):
                setattr(pod, key, value)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(pod)
        return pod

    # - MARK: 파티 삭제
    async def delete_pod(self, pod_id: int) -> bool:
        pod = await self.get_pod_by_id(pod_id)
        if pod is None:
            return False
        await self.db.delete(pod)
        await self.db.commit()
        return True

    # - MARK: 요즘 인기 있는 파티 조회
    async def get_trending_pods(
        self, user_id: int, selected_artist_id: int, page: int = 1, size: int = 20
    ) -> List[Pod]:
        """
        요즘 인기 있는 파티 조회
        조건:
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        정렬 우선순위:
        1. 최근 7일 이내 가장 많이 지원한 팟 (지원자가 동일 덕메 성향 우선)
        2. 최근 7일 이내 조회한 팟 (조회자가 동일 덕메 성향 우선)
        """
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        # 기본 조건: 마감되지 않은 파티 + 선택된 아티스트 기준
        base_conditions = and_(
            Pod.is_active == True,
            Pod.meeting_date >= now.date(),  # 마감되지 않은 파티
            Pod.selected_artist_id == selected_artist_id,  # 선택된 아티스트 기준
        )

        # 페이지네이션 계산
        offset = (page - 1) * size

        # 1순위: 최근 7일 이내 가장 많이 지원한 팟 (PodMember 기준)
        # 2순위: 최근 7일 이내 조회한 팟 (PodView 기준)
        trending_query = (
            select(
                Pod,
                func.count(PodMember.id).label("recent_applications"),
                func.count(PodView.id).label("recent_views"),
            )
            .outerjoin(
                PodMember,
                and_(Pod.id == PodMember.pod_id, PodMember.joined_at >= seven_days_ago),
            )
            .outerjoin(
                PodView,
                and_(Pod.id == PodView.pod_id, PodView.created_at >= seven_days_ago),
            )
            .where(base_conditions)
            .group_by(Pod.id)
            .order_by(
                func.count(PodMember.id).desc(),  # 1순위: 최근 지원 수
                func.count(PodView.id).desc(),  # 2순위: 최근 조회 수
                Pod.created_at.desc(),  # 3순위: 최신 생성 순
            )
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(trending_query)
        trending_pods = [row[0] for row in result.fetchall()]

        return trending_pods

    # - MARK: 마감 직전 파티 조회
    async def get_closing_soon_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> List[Pod]:
        """
        마감 직전 파티 조회
        조건:
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 에디터가 설정한 지역 (선택사항)
        정렬 우선순위:
        1. 신청 마감 시간이 24시간 이내인 모임 우선
        """
        now = datetime.now()
        twenty_four_hours_later = now + timedelta(hours=24)

        # 기본 조건: 마감되지 않은 파티 + 선택된 아티스트 기준
        base_conditions = and_(
            Pod.is_active == True,
            Pod.meeting_date >= now.date(),  # 마감되지 않은 파티
            Pod.selected_artist_id == selected_artist_id,  # 선택된 아티스트 기준
        )

        # 지역 조건 추가 (선택사항)
        if location:
            base_conditions = and_(base_conditions, Pod.address.contains(location))

        # 페이지네이션 계산
        offset = (page - 1) * size

        # 24시간 이내 마감 모임을 우선으로 정렬
        closing_soon_query = (
            select(Pod)
            .where(base_conditions)
            .order_by(
                # 24시간 이내 마감 모임 우선
                case((Pod.meeting_date <= twenty_four_hours_later.date(), 0), else_=1),
                Pod.meeting_date.asc(),
                Pod.meeting_time.asc(),
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
        now = datetime.now()
        ninety_days_ago = now - timedelta(days=90)

        # 기본 조건: 마감되지 않은 파티
        base_conditions = and_(
            Pod.is_active == True,
            Pod.meeting_date >= now.date(),  # 마감되지 않은 파티
            Pod.owner_id != user_id,  # 본인이 개설한 파티 제외
        )

        # 1순위: 참여한 팟(평점 4점 이상, 90일 이내)의 개설자가 개설한 팟
        # 사용자가 참여한 파티 조회 (PodMember + PodRating 테이블 사용)
        participated_pods_query = (
            select(Pod.id, Pod.owner_id, Pod.sub_categories, Pod.address)
            .join(PodMember, Pod.id == PodMember.pod_id)
            .join(PodRating, Pod.id == PodRating.pod_id)
            .where(
                and_(
                    PodMember.user_id == user_id,
                    PodMember.role != "owner",  # 개설자 제외
                    PodRating.user_id == user_id,  # 사용자가 평점을 준 파티
                    PodRating.rating >= 4,  # 평점 4점 이상
                    Pod.meeting_date >= ninety_days_ago.date(),
                    Pod.meeting_date <= now.date(),
                )
            )
            .order_by(Pod.meeting_date.desc())
            .limit(5)
        )

        participated_result = await self.db.execute(participated_pods_query)
        participated_pods = participated_result.fetchall()

        # 참여한 파티의 개설자 ID들
        participated_owner_ids = [pod.owner_id for pod in participated_pods]

        # 참여한 파티의 카테고리들
        participated_categories = []
        for pod in participated_pods:
            if pod.sub_categories:
                try:
                    categories = json.loads(pod.sub_categories)
                    participated_categories.extend(categories)
                except:
                    pass

        # 참여한 파티의 지역들
        participated_locations = [
            pod.address.split()[0] for pod in participated_pods if pod.address
        ]

        # 2순위: 유저가 개설한 팟에 참여한 유저(90일 이내)가 개설한 모임
        # 사용자가 개설한 파티에 참여한 사용자들 조회
        my_pods_participants_query = (
            select(PodMember.user_id)
            .join(Pod, Pod.id == PodMember.pod_id)
            .where(
                and_(
                    Pod.owner_id == user_id,
                    PodMember.role != "owner",
                    Pod.meeting_date >= ninety_days_ago.date(),
                    Pod.meeting_date <= now.date(),
                )
            )
        )

        participants_result = await self.db.execute(my_pods_participants_query)
        participant_user_ids = [row[0] for row in participants_result.fetchall()]

        # 페이지네이션 계산
        offset = (page - 1) * size

        # 1순위: 참여한 팟의 개설자가 개설한 팟
        history_based_query = select(Pod).where(
            and_(base_conditions, Pod.owner_id.in_(participated_owner_ids))
        )

        # 카테고리 우선순위 추가
        if participated_categories:
            category_priority = case(
                *[
                    (Pod.sub_categories.contains(cat), 0)
                    for cat in participated_categories
                ],
                else_=1,
            )
            history_based_query = history_based_query.order_by(category_priority)

        # 지역 우선순위 추가
        if participated_locations:
            location_priority = case(
                *[(Pod.address.contains(loc), 0) for loc in participated_locations],
                else_=1,
            )
            history_based_query = history_based_query.order_by(location_priority)

        history_based_query = history_based_query.order_by(Pod.created_at.desc())

        # 2순위: 참여한 유저가 개설한 모임 (1순위 결과가 부족할 경우)
        if len(participated_owner_ids) < size:
            remaining_size = size - len(participated_owner_ids)

            participant_created_query = (
                select(Pod)
                .where(
                    and_(
                        base_conditions,
                        Pod.owner_id.in_(participant_user_ids),
                        ~Pod.owner_id.in_(participated_owner_ids),  # 1순위와 중복 제외
                    )
                )
                .limit(remaining_size)
            )

            # 카테고리 우선순위 추가
            if participated_categories:
                category_priority = case(
                    *[
                        (Pod.sub_categories.contains(cat), 0)
                        for cat in participated_categories
                    ],
                    else_=1,
                )
                participant_created_query = participant_created_query.order_by(
                    category_priority
                )

            # 지역 우선순위 추가
            if participated_locations:
                location_priority = case(
                    *[(Pod.address.contains(loc), 0) for loc in participated_locations],
                    else_=1,
                )
                participant_created_query = participant_created_query.order_by(
                    location_priority
                )

            participant_created_query = participant_created_query.order_by(
                Pod.created_at.desc()
            )

        # 최종 쿼리 실행
        history_based_query = history_based_query.offset(offset).limit(size)
        result = await self.db.execute(history_based_query)
        history_based_pods = result.scalars().all()

        return history_based_pods

    # - MARK: 인기 최고 카테고리 파티 조회
    async def get_popular_categories_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> List[Pod]:
        """
        인기 최고 카테고리 파티 조회
        조건:
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 최근 일주일 기준 가장 많이 개설된 카테고리 && 최근 일주일 기준 가장 조회가 많은 카테고리
        정렬 우선순위:
        1. 에디터가 설정한 지역의 모임 우선 (선택사항)
        2. 조회수 높은 순
        """
        now = datetime.now()
        one_week_ago = now - timedelta(days=7)

        # 기본 조건: 마감되지 않은 파티
        base_conditions = and_(
            Pod.is_active == True, Pod.meeting_date >= now.date()  # 마감되지 않은 파티
        )

        # 지역 조건 추가 (선택사항)
        if location:
            base_conditions = and_(base_conditions, Pod.address.contains(location))

        # 최근 일주일 기준 가장 많이 개설된 카테고리 조회
        popular_categories_by_creation_query = (
            select(Pod.sub_categories, func.count(Pod.id).label("creation_count"))
            .where(
                and_(
                    Pod.is_active == True,
                    Pod.created_at >= one_week_ago,
                    Pod.sub_categories.isnot(None),
                )
            )
            .group_by(Pod.sub_categories)
            .order_by(func.count(Pod.id).desc())
            .limit(5)
        )

        creation_result = await self.db.execute(popular_categories_by_creation_query)
        popular_categories_by_creation = creation_result.fetchall()

        # 최근 일주일 기준 가장 조회가 많은 카테고리 조회
        popular_categories_by_views_query = (
            select(Pod.sub_categories, func.count(PodView.id).label("view_count"))
            .join(PodView, Pod.id == PodView.pod_id)
            .where(
                and_(
                    Pod.is_active == True,
                    PodView.created_at >= one_week_ago,
                    Pod.sub_categories.isnot(None),
                )
            )
            .group_by(Pod.sub_categories)
            .order_by(func.count(PodView.id).desc())
            .limit(5)
        )

        views_result = await self.db.execute(popular_categories_by_views_query)
        popular_categories_by_views = views_result.fetchall()

        # 인기 카테고리 통합 (개설 우선, 조회 보조)
        popular_categories = []
        seen_categories = set()

        # 1순위: 개설 기준 인기 카테고리
        for category_row in popular_categories_by_creation:
            if (
                category_row.sub_categories
                and category_row.sub_categories not in seen_categories
            ):
                popular_categories.append(category_row.sub_categories)
                seen_categories.add(category_row.sub_categories)

        # 2순위: 조회 기준 인기 카테고리 (개설 기준에 없는 것만)
        for category_row in popular_categories_by_views:
            if (
                category_row.sub_categories
                and category_row.sub_categories not in seen_categories
            ):
                popular_categories.append(category_row.sub_categories)
                seen_categories.add(category_row.sub_categories)

        # 페이지네이션 계산
        offset = (page - 1) * size

        # 인기 카테고리 기반 파티 조회
        if popular_categories:
            # 카테고리 우선순위 설정
            category_priority = case(
                *[
                    (Pod.sub_categories == cat, idx)
                    for idx, cat in enumerate(popular_categories)
                ],
                else_=len(popular_categories),
            )

            popular_categories_query = (
                select(Pod, func.count(PodView.id).label("view_count"))
                .outerjoin(PodView, Pod.id == PodView.pod_id)
                .where(base_conditions)
                .group_by(Pod.id)
                .order_by(
                    category_priority,
                    func.count(PodView.id).desc(),  # 조회수 높은 순
                    Pod.created_at.desc(),  # 최신순
                )
                .offset(offset)
                .limit(size)
            )
        else:
            # 인기 카테고리가 없으면 최신 파티 조회
            popular_categories_query = (
                select(Pod)
                .where(base_conditions)
                .order_by(Pod.created_at.desc())
                .offset(offset)
                .limit(size)
            )

        result = await self.db.execute(popular_categories_query)
        if popular_categories:
            popular_categories_pods = [row[0] for row in result.fetchall()]
        else:
            popular_categories_pods = result.scalars().all()

        return popular_categories_pods

    # - MARK: 평점 관련 메서드
    async def add_pod_rating(
        self, pod_id: int, user_id: int, rating: int, review: Optional[str] = None
    ) -> PodRating:
        """파티 평점 추가/수정"""
        # 기존 평점이 있는지 확인
        existing_rating = await self.db.execute(
            select(PodRating).where(
                and_(PodRating.pod_id == pod_id, PodRating.user_id == user_id)
            )
        )
        existing_rating = existing_rating.scalar_one_or_none()

        if existing_rating:
            # 기존 평점 수정
            existing_rating.rating = rating
            existing_rating.review = review
            existing_rating.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(existing_rating)
            return existing_rating
        else:
            # 새 평점 추가
            new_rating = PodRating(
                pod_id=pod_id, user_id=user_id, rating=rating, review=review
            )
            self.db.add(new_rating)
            await self.db.commit()
            await self.db.refresh(new_rating)
            return new_rating

    async def get_pod_ratings(self, pod_id: int) -> List[PodRating]:
        """파티 평점 목록 조회"""
        result = await self.db.execute(
            select(PodRating)
            .where(PodRating.pod_id == pod_id)
            .order_by(PodRating.created_at.desc())
        )
        return result.scalars().all()

    async def get_pod_average_rating(self, pod_id: int) -> Optional[float]:
        """파티 평균 평점 조회"""
        result = await self.db.execute(
            select(func.avg(PodRating.rating)).where(PodRating.pod_id == pod_id)
        )
        avg_rating = result.scalar()
        return round(avg_rating, 2) if avg_rating else None

    # - MARK: 조회수 관련 메서드
    async def add_pod_view(
        self,
        pod_id: int,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PodView:
        """파티 조회수 추가"""
        # 중복 조회 방지 (같은 사용자/IP가 같은 파티를 중복 조회하는 것 방지)
        existing_view = await self.db.execute(
            select(PodView).where(
                and_(
                    PodView.pod_id == pod_id,
                    PodView.user_id == user_id,
                    PodView.ip_address == ip_address,
                )
            )
        )
        existing_view = existing_view.scalar_one_or_none()

        if not existing_view:
            new_view = PodView(
                pod_id=pod_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(new_view)
            await self.db.commit()
            await self.db.refresh(new_view)
            return new_view
        return existing_view

    async def get_pod_view_count(self, pod_id: int) -> int:
        """파티 조회수 조회"""
        result = await self.db.execute(
            select(func.count(PodView.id)).where(PodView.pod_id == pod_id)
        )
        return result.scalar() or 0

    async def get_pods_by_view_count(self, limit: int = 10) -> List[Pod]:
        """조회수 기준 인기 파티 조회"""
        result = await self.db.execute(
            select(Pod, func.count(PodView.id).label("view_count"))
            .outerjoin(PodView, Pod.id == PodView.pod_id)
            .where(Pod.is_active == True)
            .group_by(Pod.id)
            .order_by(func.count(PodView.id).desc())
            .limit(limit)
        )
        return [row[0] for row in result.fetchall()]

    async def get_joined_users_count(self, pod_id: int) -> int:
        """파티 참여자 수 조회"""
        result = await self.db.execute(
            select(func.count(PodMember.id)).where(PodMember.pod_id == pod_id)
        )
        return result.scalar() or 0

    async def get_like_count(self, pod_id: int) -> int:
        """파티 좋아요 수 조회"""
        from app.models.pod.pod_like import PodLike

        result = await self.db.execute(
            select(func.count(PodLike.id)).where(PodLike.pod_id == pod_id)
        )
        return result.scalar() or 0

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
        status: PodStatus = PodStatus.RECRUITING,
    ) -> Pod:
        """파티 생성 (채팅방 포함)"""
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
            status=status,
        )

        # Sendbird 채팅방 생성
        try:
            from app.services.sendbird_service import SendbirdService

            sendbird_service = SendbirdService()

            # 채널 URL 생성 (pod_{pod_id}_chat 형식)
            channel_url = f"pod_{pod.id}_chat"

            # 채널 생성
            channel_data = await sendbird_service.create_group_channel(
                channel_url=channel_url,
                name=f"{title} 채팅방",
                user_ids=[str(owner_id)],  # 파티 생성자만 초기 멤버
                data={"pod_id": pod.id, "pod_title": title, "type": "pod_chat"},
            )

            if channel_data:
                # 채팅방 URL을 파티에 저장
                pod.chat_channel_url = channel_url
                await self.db.commit()
                await self.db.refresh(pod)

        except ValueError as e:
            print(f"Sendbird 설정 오류: {e}")
            # Sendbird 설정이 없으면 채팅방 없이 파티만 생성
        except Exception as e:
            print(f"Sendbird 채팅방 생성 실패: {e}")
            # 채팅방 생성 실패해도 파티는 생성됨

        return pod
