"""Review DTO 변환 서비스"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.pods.models import PodReview
from app.features.pods.models.pod_models import Pod
from app.features.pods.schemas import PodDto, PodReviewDto
from app.features.pods.services.pod_dto_service import PodDtoService
from app.features.users.models import User
from app.features.users.repositories import UserRepository
from app.features.users.schemas import UserDto


class ReviewDtoService:
    """Review DTO 변환을 담당하는 서비스"""

    def __init__(self, session: AsyncSession, user_repo: UserRepository):
        self._session = session
        self._user_repo = user_repo

    async def convert_to_dto(self, review: PodReview) -> PodReviewDto:
        """PodReview 모델을 PodReviewDto로 변환"""
        try:
            # PodDto 생성
            simple_pod = await self._create_pod_dto(review)

            # UserDto 생성
            user_dto = await self._create_user_dto(review)

            if review.id is None or review.rating is None:
                raise ValueError("후기 정보가 올바르지 않습니다.")

            review_created_at = review.created_at or datetime.now(timezone.utc)
            review_updated_at = review.updated_at or datetime.now(timezone.utc)

            return PodReviewDto(
                id=review.id,
                pod=simple_pod,
                user=user_dto,
                rating=review.rating,
                content=review.content or "",
                created_at=review_created_at,
                updated_at=review_updated_at,
            )

        except Exception:
            raise

    async def _create_pod_dto(self, review: PodReview) -> PodDto:
        """Review에서 PodDto 생성"""
        try:
            pod_raw = review.pod if hasattr(review, "pod") and review.pod else None
            pod: Pod | None = pod_raw if isinstance(pod_raw, Pod) else None

            if pod:
                return PodDtoService.convert_to_dto(pod)
            return PodDtoService.create_empty_dto()
        except Exception:
            return PodDtoService.create_empty_dto()

    async def _create_user_dto(self, review: PodReview) -> UserDto:
        """Review에서 UserDto 생성"""
        try:
            user_raw = review.user if hasattr(review, "user") and review.user else None
            user: User | None = user_raw if isinstance(user_raw, User) else None

            # 성향 타입 조회
            user_tendency_type = ""
            if user and user.id:
                user_tendency_type = await self._user_repo.get_user_tendency_type(
                    user.id
                )

            return UserDto(
                id=user.id or 0 if user else 0,
                nickname=user.nickname or "" if user else "",
                profile_image=user.profile_image or "" if user else "",
                intro=user.intro or "" if user else "",
                tendency_type=user_tendency_type or "",
                is_following=False,
            )
        except Exception:
            return UserDto(
                id=0,
                nickname="",
                profile_image="",
                intro="",
                tendency_type="",
                is_following=False,
            )

    def _parse_sub_categories(self, pod: Pod | None) -> list:
        """Pod의 sub_categories 파싱 - PodDtoService로 위임"""
        if not pod:
            return []
        return PodDtoService.parse_sub_categories(pod.sub_categories)
