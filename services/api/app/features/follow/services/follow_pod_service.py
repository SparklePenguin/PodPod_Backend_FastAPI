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

            from app.features.pods.models import PodStatus

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

            # PodDetail에서 정보 가져오기
            pod_detail = pod.detail if pod.detail else None
            
            pod_dto = PodDetailDto(
                id=pod_id,
                owner_id=pod.owner_id,
                title=pod.title or "",
                description=pod_detail.description if pod_detail else "",
                image_url=pod_detail.image_url if pod_detail else None,
                thumbnail_url=pod.thumbnail_url,
                sub_categories=pod_sub_categories,
                capacity=pod.capacity or 0,
                place=pod.place or "",
                address=pod_detail.address if pod_detail else "",
                sub_address=pod_detail.sub_address if pod_detail else None,
                x=pod_detail.x if pod_detail else None,
                y=pod_detail.y if pod_detail else None,
                meeting_date=pod.meeting_date if pod.meeting_date else None,
                meeting_time=pod.meeting_time if pod.meeting_time else None,
                selected_artist_id=pod.selected_artist_id,
                status=pod_status_enum,
                is_del=pod.is_del if pod.is_del else False,
                chat_room_id=pod.chat_room_id,
                images=[],  # 이미지는 별도로 로드 필요
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
