"""Review Use Case - 비즈니스 로직 처리"""

from app.common.schemas import PageDto
from app.features.pods.exceptions import (
    PodNotFoundException,
    ReviewAlreadyExistsException,
    ReviewNotFoundException,
    ReviewPermissionDeniedException,
)
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.schemas import (
    PodReviewCreateRequest,
    PodReviewDto,
    PodReviewUpdateRequest,
)
from app.features.pods.services.review_service import ReviewService
from sqlalchemy.ext.asyncio import AsyncSession


class ReviewUseCase:
    """Review 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        review_service: ReviewService,
        pod_repo: PodRepository,
        review_repo: PodReviewRepository,
    ):
        self._session = session
        self._review_service = review_service
        self._pod_repo = pod_repo
        self._review_repo = review_repo

    # MARK: - 후기 생성
    async def create_review(
        self, user_id: int, request: PodReviewCreateRequest
    ) -> PodReviewDto:
        """후기 생성 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(request.pod_id)
        if pod is None:
            raise PodNotFoundException(request.pod_id)

        # 서비스 로직 호출
        try:
            result = await self._review_service.create_review(user_id, request)
            await self._session.commit()
            return result
        except ReviewAlreadyExistsException:
            await self._session.rollback()
            raise
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - ID로 후기 조회
    async def get_review_by_id(self, review_id: int) -> PodReviewDto:
        """ID로 후기 조회 (비즈니스 로직 검증)"""
        # 서비스 로직 호출
        return await self._review_service.get_review_by_id(review_id)

    # MARK: - 특정 파티의 후기 목록 조회
    async def get_reviews_by_pod(
        self, pod_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 파티의 후기 목록 조회 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        # 서비스 로직 호출
        return await self._review_service.get_reviews_by_pod(pod_id, page, size)

    # MARK: - 특정 사용자가 작성한 후기 목록 조회
    async def get_reviews_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 작성한 후기 목록 조회 (비즈니스 로직 검증)"""
        # 서비스 로직 호출
        return await self._review_service.get_reviews_by_user(user_id, page, size)

    # MARK: - 특정 사용자가 받은 후기 목록 조회
    async def get_reviews_received_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 받은 후기 목록 조회 (비즈니스 로직 검증)"""
        # 서비스 로직 호출
        return await self._review_service.get_reviews_received_by_user(
            user_id, page, size
        )

    # MARK: - 후기 수정
    async def update_review(
        self, review_id: int, user_id: int, request: PodReviewUpdateRequest
    ) -> PodReviewDto:
        """후기 수정 (비즈니스 로직 검증)"""
        # 후기 존재 및 작성자 확인
        review = await self._review_repo.get_review_by_id(review_id)
        if not review:
            raise ReviewNotFoundException(review_id)

        if review.user_id != user_id:
            raise ReviewPermissionDeniedException(review_id, user_id)

        # 서비스 로직 호출
        try:
            result = await self._review_service.update_review(
                review_id, user_id, request
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 후기 삭제
    async def delete_review(self, review_id: int, user_id: int) -> bool:
        """후기 삭제 (비즈니스 로직 검증)"""
        # 후기 존재 및 작성자 확인
        review = await self._review_repo.get_review_by_id(review_id)
        if not review:
            raise ReviewNotFoundException(review_id)

        if review.user_id != user_id:
            raise ReviewPermissionDeniedException(review_id, user_id)

        # 서비스 로직 호출
        try:
            result = await self._review_service.delete_review(review_id, user_id)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티별 후기 통계 조회
    async def get_review_stats_by_pod(self, pod_id: int) -> dict:
        """파티별 후기 통계 조회 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        # 서비스 로직 호출
        return await self._review_service.get_review_stats_by_pod(pod_id)
