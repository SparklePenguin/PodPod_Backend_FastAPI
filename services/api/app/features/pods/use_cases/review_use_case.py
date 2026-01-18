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
from app.features.pods.services.review_dto_service import ReviewDtoService
from app.features.pods.services.review_notification_service import (
    ReviewNotificationService,
)
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class ReviewUseCase:
    """Review 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        review_repo: PodReviewRepository,
        pod_repo: PodRepository,
        user_repo: UserRepository,
        notification_service: ReviewNotificationService,
    ):
        self._session = session
        self._review_repo = review_repo
        self._pod_repo = pod_repo
        self._user_repo = user_repo
        self._notification_service = notification_service
        self._dto_service = ReviewDtoService(session, user_repo)

    # MARK: - 후기 생성
    async def create_review(
        self, user_id: int, request: PodReviewCreateRequest
    ) -> PodReviewDto:
        """후기 생성"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(request.pod_id)
        if pod is None:
            raise PodNotFoundException(request.pod_id)

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
        await self._session.commit()

        if not review or review.id is None:
            raise ValueError("후기 생성에 실패했습니다.")

        # 리뷰 생성 알림 전송
        await self._notification_service.send_review_created_notification(
            review.id, request.pod_id, user_id
        )

        return await self._dto_service.convert_to_dto(review)

    # MARK: - ID로 후기 조회
    async def get_review_by_id(self, review_id: int) -> PodReviewDto:
        """ID로 후기 조회"""
        review = await self._review_repo.get_review_by_id(review_id)
        if not review:
            raise ReviewNotFoundException(review_id)

        return await self._dto_service.convert_to_dto(review)

    # MARK: - 특정 파티의 후기 목록 조회
    async def get_reviews_by_pod(
        self, pod_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 파티의 후기 목록 조회"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        reviews, total_count = await self._review_repo.get_reviews_by_pod(
            pod_id, page, size
        )

        review_dtos = []
        for review in reviews:
            review_dto = await self._dto_service.convert_to_dto(review)
            review_dtos.append(review_dto)

        return PageDto.create(
            items=review_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # MARK: - 특정 사용자가 작성한 후기 목록 조회
    async def get_reviews_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 작성한 후기 목록 조회"""
        reviews, total_count = await self._review_repo.get_reviews_by_user(
            user_id, page, size
        )

        review_dtos = []
        for review in reviews:
            review_dto = await self._dto_service.convert_to_dto(review)
            review_dtos.append(review_dto)

        return PageDto.create(
            items=review_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # MARK: - 특정 사용자가 받은 후기 목록 조회
    async def get_reviews_received_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 참여한 파티에 대한 받은 리뷰 목록 조회 (본인이 작성한 리뷰 제외)"""
        reviews, total_count = await self._review_repo.get_reviews_received_by_user(
            user_id, page, size
        )

        review_dtos = []
        for review in reviews:
            review_dto = await self._dto_service.convert_to_dto(review)
            review_dtos.append(review_dto)

        return PageDto.create(
            items=review_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # MARK: - 후기 수정
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
        await self._session.commit()

        if not updated_review:
            raise ReviewNotFoundException(review_id)

        return await self._dto_service.convert_to_dto(updated_review)

    # MARK: - 후기 삭제
    async def delete_review(self, review_id: int, user_id: int) -> bool:
        """후기 삭제"""
        # 후기 존재 및 작성자 확인
        review = await self._review_repo.get_review_by_id(review_id)
        if not review:
            raise ReviewNotFoundException(review_id)

        if review.user_id != user_id:
            raise ReviewPermissionDeniedException(review_id, user_id)

        result = await self._review_repo.delete_review(review_id)
        await self._session.commit()

        return result

    # MARK: - 파티별 후기 통계 조회
    async def get_review_stats_by_pod(self, pod_id: int) -> dict:
        """파티별 후기 통계 조회"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        return await self._review_repo.get_review_stats_by_pod(pod_id)
