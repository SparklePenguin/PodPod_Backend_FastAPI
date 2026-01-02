from app.common.schemas.page_dto import PageDto
from app.features.follow.repositories.follow_pod_repository import FollowPodRepository
from app.features.follow.services.follow_utils import create_page_dto
from app.features.pods.models import (
    AccompanySubCategory,
    EtcSubCategory,
    GoodsSubCategory,
    TourSubCategory,
)
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.schemas import PodDetailDto
from app.features.pods.services.review_service import ReviewService
from sqlalchemy.ext.asyncio import AsyncSession


class FollowPodService:
    """팔로우한 사용자의 파티 서비스"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._follow_pod_repo = FollowPodRepository(session)
        self._pod_repo = PodRepository(session)
        self._review_repo = PodReviewRepository(session)

    # - MARK: 팔로우하는 사용자가 만든 파티 목록 조회
    async def get_following_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDetailDto]:
        """팔로우하는 사용자가 만든 파티 목록 조회"""
        pods, total_count = await self._follow_pod_repo.get_following_pods(
            user_id, page, size
        )

        pod_dtos = []
        for pod in pods:
            if pod.id is None:
                continue
            pod_id = pod.id

            # 각 파티의 참여자 수와 좋아요 수 계산
            joined_users_count = await self._pod_repo.get_joined_users_count(pod_id)
            like_count = await self._pod_repo.get_like_count(pod_id)
            view_count = await self._pod_repo.get_view_count(pod_id)

            # 사용자가 좋아요했는지 확인
            is_liked = await self._pod_repo.is_liked_by_user(pod_id, user_id)

            # meeting_date와 meeting_time을 timestamp로 변환 (UTC로 저장된 값이므로 UTC로 해석)
            def _convert_to_timestamp(meeting_date, meeting_time):
                """date와 time 객체를 UTC로 해석하여 timestamp로 변환"""
                if meeting_date is None:
                    return None
                from datetime import datetime, timezone
                from datetime import time as time_module

                if meeting_time is None:
                    dt = datetime.combine(
                        meeting_date, time_module.min, tzinfo=timezone.utc
                    )
                else:
                    dt = datetime.combine(
                        meeting_date, meeting_time, tzinfo=timezone.utc
                    )
                return int(dt.timestamp() * 1000)  # milliseconds

            # PodDetailDto를 수동으로 생성하여 MissingGreenlet 오류 방지
            # 후기 목록 조회
            reviews = await self._review_repo.get_all_reviews_by_pod(pod_id)
            review_service = ReviewService(self._session)
            review_dtos = []
            for review in reviews:
                review_dto = await review_service._convert_to_dto(review)
                review_dtos.append(review_dto)

            # Pod 속성 추출
            pod_sub_categories = pod.sub_categories

            # sub_categories가 문자열인 경우 파싱 필요할 수 있음
            if pod_sub_categories is None:
                pod_sub_categories = []
            elif isinstance(pod_sub_categories, str):
                import json

                try:
                    parsed = json.loads(pod_sub_categories) if pod_sub_categories else []
                    pod_sub_categories = parsed if isinstance(parsed, list) else []
                except (ValueError, TypeError, json.JSONDecodeError):
                    pod_sub_categories = []
            elif isinstance(pod_sub_categories, list):
                pod_sub_categories = pod_sub_categories
            else:
                pod_sub_categories = []
            
            # 카테고리 검증은 use case에서 처리 (이미 저장된 데이터는 그대로 표시)

            from datetime import datetime, timezone

            from app.features.pods.models.pod.pod_status import PodStatus

            if pod.owner_id is None:
                continue  # owner_id가 없으면 건너뛰기

            pod_status_enum = pod.status
            if pod_status_enum is None:
                pod_status_enum = PodStatus.RECRUITING
            elif isinstance(pod_status_enum, str):
                try:
                    pod_status_enum = PodStatus(pod_status_enum.upper())
                except ValueError:
                    pod_status_enum = PodStatus.RECRUITING

            pod_created_at = pod.created_at
            if pod_created_at is None:
                pod_created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            pod_updated_at = pod.updated_at
            if pod_updated_at is None:
                pod_updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            pod_dto = PodDetailDto(
                id=pod_id,
                owner_id=pod.owner_id,
                title=pod.title or "",
                description=pod.description or "",
                image_url=pod.image_url,
                thumbnail_url=pod.thumbnail_url,
                sub_categories=pod_sub_categories,
                capacity=pod.capacity or 0,
                place=pod.place or "",
                address=pod.address or "",
                sub_address=pod.sub_address,
                x=pod.x,
                y=pod.y,
                meeting_date=_convert_to_timestamp(pod.meeting_date, pod.meeting_time),
                selected_artist_id=pod.selected_artist_id,
                status=pod_status_enum,
                chat_channel_url=pod.chat_channel_url,
                created_at=pod_created_at,
                updated_at=pod_updated_at,
                # 실제 값 설정
                is_liked=is_liked,
                my_application=None,
                applications=[],
                view_count=view_count,
                joined_users_count=joined_users_count,
                like_count=like_count,
                joined_users=[],  # 팔로우 파티 목록에서는 빈 배열로 설정
                reviews=review_dtos,  # 후기 목록
            )

            pod_dtos.append(pod_dto)

        return create_page_dto(pod_dtos, page, size, total_count)
