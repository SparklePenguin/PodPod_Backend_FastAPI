from datetime import datetime, time, timezone

from app.common.schemas import PageDto
from app.features.pods.exceptions import (
    ReviewAlreadyExistsException,
    ReviewNotFoundException,
    ReviewPermissionDeniedException,
)
from app.features.pods.models import PodReview
from app.features.pods.models.pod_models import Pod
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.schemas import (
    PodDto,
    PodReviewCreateRequest,
    PodReviewDto,
    PodReviewUpdateRequest,
)
from app.features.pods.services.review_notification_service import (
    ReviewNotificationService,
)
from app.features.users.models import User
from app.features.users.repositories import UserRepository
from app.features.users.schemas import UserDto
from sqlalchemy.ext.asyncio import AsyncSession


def _convert_to_combined_timestamp(meeting_date, meeting_time):
    """date와 time 객체를 UTC로 해석하여 하나의 timestamp로 변환"""
    if meeting_date is None:
        return None
    if meeting_time is None:
        # time이 없으면 date만 사용 (00:00:00)
        dt = datetime.combine(meeting_date, time.min, tzinfo=timezone.utc)
    else:
        # date와 time을 결합 (UTC로 해석)
        dt = datetime.combine(meeting_date, meeting_time, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)  # milliseconds


class ReviewService:
    """Pod 후기 관련 비즈니스 로직을 처리하는 서비스"""

    def __init__(
        self,
        session: AsyncSession,
        review_repo: PodReviewRepository,
        user_repo: UserRepository,
        notification_service: ReviewNotificationService,
    ):
        self._session = session
        self._review_repo = review_repo
        self._user_repo = user_repo
        self._notification_service = notification_service

    # - MARK: 후기 생성
    async def create_review(
        self, user_id: int, request: PodReviewCreateRequest
    ) -> PodReviewDto:
        """후기 생성"""
        # 이미 작성한 후기가 있는지 확인
        existing_review = await self._review_repo.get_review_by_pod_and_user(
            request.pod_id, user_id
        )
        if existing_review:
            raise ReviewAlreadyExistsException(request.pod_id, user_id)

        # 후기 생성
        review = await self._review_repo.create_review(
            pod_id=request.pod_id,
            user_id=user_id,
            rating=request.rating,
            content=request.content,
        )

        if not review:
            raise ValueError("후기 생성에 실패했습니다.")

        if review.id is None:
            raise ValueError("후기 생성 후 ID를 가져올 수 없습니다.")

        # 리뷰 생성 알림 전송
        await self._notification_service.send_review_created_notification(
            review.id, request.pod_id, user_id
        )

        return await self._convert_to_dto(review)

    # - MARK: ID로 후기 조회
    async def get_review_by_id(self, review_id: int) -> PodReviewDto:
        """ID로 후기 조회"""
        review = await self._review_repo.get_review_by_id(review_id)
        if not review:
            raise ReviewNotFoundException(review_id)

        return await self._convert_to_dto(review)

    # - MARK: 특정 파티의 후기 목록 조회
    async def get_reviews_by_pod(
        self, pod_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 파티의 후기 목록 조회"""
        reviews, total_count = await self._review_repo.get_reviews_by_pod(
            pod_id, page, size
        )

        review_dtos = []
        for review in reviews:
            review_dto = await self._convert_to_dto(review)
            review_dtos.append(review_dto)

        return PageDto.create(
            items=review_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # - MARK: 특정 사용자가 작성한 후기 목록 조회
    async def get_reviews_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 작성한 후기 목록 조회"""
        reviews, total_count = await self._review_repo.get_reviews_by_user(
            user_id, page, size
        )

        review_dtos = []
        for review in reviews:
            review_dto = await self._convert_to_dto(review)
            review_dtos.append(review_dto)

        return PageDto.create(
            items=review_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # - MARK: 특정 사용자가 받은 후기 목록 조회
    async def get_reviews_received_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 참여한 파티에 대한 받은 리뷰 목록 조회 (본인이 작성한 리뷰 제외)"""
        reviews, total_count = await self._review_repo.get_reviews_received_by_user(
            user_id, page, size
        )

        review_dtos = []
        for review in reviews:
            review_dto = await self._convert_to_dto(review)
            review_dtos.append(review_dto)

        return PageDto.create(
            items=review_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # - MARK: 후기 수정
    async def update_review(
        self, review_id: int, user_id: int, request: PodReviewUpdateRequest
    ) -> PodReviewDto:
        """후기 수정"""
        # 후기 존재 및 작성자 확인
        review = await self._review_repo.get_review_by_id(review_id)
        if not review:
            raise ReviewNotFoundException(review_id)

        if review.user_id != user_id:
            raise ReviewPermissionDeniedException(review_id, user_id)

        # 후기 수정
        updated_review = await self._review_repo.update_review(
            review_id=review_id, rating=request.rating, content=request.content
        )

        if not updated_review:
            raise ReviewNotFoundException(review_id)

        return await self._convert_to_dto(updated_review)

    # - MARK: 후기 삭제
    async def delete_review(self, review_id: int, user_id: int) -> bool:
        """후기 삭제"""
        # 후기 존재 및 작성자 확인
        review = await self._review_repo.get_review_by_id(review_id)
        if not review:
            raise ReviewNotFoundException(review_id)

        if review.user_id != user_id:
            raise ReviewPermissionDeniedException(review_id, user_id)

        return await self._review_repo.delete_review(review_id)

    # - MARK: 파티별 후기 통계 조회
    async def get_review_stats_by_pod(self, pod_id: int) -> dict:
        """파티별 후기 통계 조회"""
        return await self._review_repo.get_review_stats_by_pod(pod_id)

    # - MARK: PodReview 모델을 PodReviewDto로 변환
    async def _convert_to_dto(self, review: PodReview) -> PodReviewDto:
        """PodReview 모델을 PodReviewDto로 변환

        PodDto와 UserDto는 SQLAlchemy 모델과 구조가 다르므로 수동 변환이 필요합니다:
        - PodDto: sub_categories 변환, meeting_date/meeting_time 결합 등
        - UserDto: tendency_type 별도 조회 필요
        """
        try:
            # sub_categories 처리 (JSON 문자열을 리스트로 변환)
            sub_categories = []
            try:
                if hasattr(review, "pod") and review.pod:
                    sub_categories = review.pod.sub_categories or []
                    if isinstance(sub_categories, str):
                        import json

                        sub_categories = json.loads(sub_categories)
            except Exception:
                sub_categories = []

            # PodDto 생성 - 안전하게 처리
            try:
                pod_raw = review.pod if hasattr(review, "pod") and review.pod else None
                pod: Pod | None = pod_raw if isinstance(pod_raw, Pod) else None
                from datetime import date
                from datetime import time as time_module

                # sub_categories 파싱
                pod_sub_categories = []
                if pod and pod.sub_categories:
                    if isinstance(pod.sub_categories, str):
                        import json

                        try:
                            pod_sub_categories = json.loads(pod.sub_categories)
                        except Exception:
                            pod_sub_categories = []
                    elif isinstance(pod.sub_categories, list):
                        pod_sub_categories = pod.sub_categories

                simple_pod = PodDto(
                    id=pod.id or 0 if pod else 0,
                    owner_id=pod.owner_id or 0 if pod else 0,
                    title=pod.title or "" if pod else "",
                    thumbnail_url=(pod.thumbnail_url or "") if pod else "",
                    sub_categories=pod_sub_categories,
                    selected_artist_id=pod.selected_artist_id if pod else None,
                    capacity=pod.capacity or 0 if pod else 0,
                    place=pod.place or "" if pod else "",
                    meeting_date=pod.meeting_date
                    if pod and pod.meeting_date
                    else date.today(),
                    meeting_time=pod.meeting_time
                    if pod and pod.meeting_time
                    else time_module.min,
                    status=pod.status,
                    is_del=pod.is_del if pod else False,
                    created_at=pod.created_at
                    if pod and pod.created_at
                    else datetime.now(timezone.utc),
                    updated_at=pod.updated_at
                    if pod and pod.updated_at
                    else datetime.now(timezone.utc),
                )
            except Exception:
                # 기본값으로 PodDto 생성
                from datetime import date
                from datetime import time as time_module

                from app.features.pods.models import PodStatus

                simple_pod = PodDto(
                    id=0,
                    owner_id=0,
                    title="",
                    thumbnail_url="",
                    sub_categories=[],
                    selected_artist_id=None,
                    capacity=0,
                    place="",
                    meeting_date=date.today(),
                    meeting_time=time_module.min,
                    status=PodStatus.RECRUITING,
                    is_del=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

            # UserDto 생성 - 안전하게 처리
            try:
                # 성향 타입 조회 (repository 사용)
                user_tendency_type = ""
                user_raw = (
                    review.user if hasattr(review, "user") and review.user else None
                )
                user: User | None = user_raw if isinstance(user_raw, User) else None
                if user and user.id:
                    user_tendency_type = await self._user_repo.get_user_tendency_type(
                        user.id
                    )

                user_follow = UserDto(
                    id=user.id or 0 if user else 0,
                    nickname=user.nickname or "" if user else "",
                    profile_image=user.profile_image or "" if user else "",
                    intro=user.intro or "" if user else "",
                    tendency_type=user_tendency_type or "",
                    is_following=False,  # 필요시 별도 조회
                )
            except Exception:
                # 기본값으로 UserDto 생성
                user_follow = UserDto(
                    id=0,
                    nickname="",
                    profile_image="",
                    intro="",
                    tendency_type="",
                    is_following=False,
                )

            if review.id is None or review.rating is None:
                raise ValueError("후기 정보가 올바르지 않습니다.")

            review_created_at = review.created_at
            if review_created_at is None:
                review_created_at = datetime.now(timezone.utc).replace(tzinfo=None)

            review_updated_at = review.updated_at
            if review_updated_at is None:
                review_updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            result = PodReviewDto(
                id=review.id,
                pod=simple_pod,
                user=user_follow,
                rating=review.rating,
                content=review.content or "",
                created_at=review_created_at,
                updated_at=review_updated_at,
            )

            return result

        except Exception:
            raise
