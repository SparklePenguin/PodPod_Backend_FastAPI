from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.pod_review import PodReviewCRUD
from app.schemas.pod_review import (
    PodReviewCreateRequest,
    PodReviewUpdateRequest,
    PodReviewDto,
    SimplePodDto,
)
from app.schemas.follow import SimpleUserDto
from app.schemas.common import PageDto
from app.models.pod_review import PodReview
from app.core.logging_config import get_logger
import math

logger = get_logger("pod_review_service")


class PodReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = PodReviewCRUD(db)

    async def create_review(
        self, user_id: int, request: PodReviewCreateRequest
    ) -> Optional[PodReviewDto]:
        """후기 생성"""
        try:
            # 이미 작성한 후기가 있는지 확인
            existing_review = await self.crud.get_review_by_pod_and_user(
                request.pod_id, user_id
            )
            if existing_review:
                raise ValueError("이미 해당 파티에 후기를 작성했습니다.")

            # 후기 생성
            review = await self.crud.create_review(
                pod_id=request.pod_id,
                user_id=user_id,
                rating=request.rating,
                content=request.content,
            )

            if not review:
                logger.error(
                    f"후기 생성 실패: user_id={user_id}, pod_id={request.pod_id}"
                )
                return None

            logger.info(f"후기 생성 성공: review_id={review.id}")
            return await self._convert_to_dto(review)

        except Exception as e:
            logger.error(
                f"후기 생성 중 예외 발생: {type(e).__name__}: {str(e)}", exc_info=True
            )
            raise

    async def get_review_by_id(self, review_id: int) -> Optional[PodReviewDto]:
        """ID로 후기 조회"""
        review = await self.crud.get_review_by_id(review_id)
        if not review:
            return None

        return await self._convert_to_dto(review)

    async def get_reviews_by_pod(
        self, pod_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 파티의 후기 목록 조회"""
        reviews, total_count = await self.crud.get_reviews_by_pod(pod_id, page, size)

        review_dtos = []
        for review in reviews:
            review_dto = await self._convert_to_dto(review)
            review_dtos.append(review_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodReviewDto](
            items=review_dtos,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def get_reviews_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 작성한 후기 목록 조회"""
        reviews, total_count = await self.crud.get_reviews_by_user(user_id, page, size)

        review_dtos = []
        for review in reviews:
            review_dto = await self._convert_to_dto(review)
            review_dtos.append(review_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodReviewDto](
            items=review_dtos,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def update_review(
        self, review_id: int, user_id: int, request: PodReviewUpdateRequest
    ) -> Optional[PodReviewDto]:
        """후기 수정"""
        # 후기 존재 및 작성자 확인
        review = await self.crud.get_review_by_id(review_id)
        if not review:
            raise ValueError("후기를 찾을 수 없습니다.")

        if review.user_id != user_id:
            raise ValueError("본인이 작성한 후기만 수정할 수 있습니다.")

        # 후기 수정
        updated_review = await self.crud.update_review(
            review_id=review_id,
            rating=request.rating,
            content=request.content,
        )

        if not updated_review:
            return None

        return await self._convert_to_dto(updated_review)

    async def delete_review(self, review_id: int, user_id: int) -> bool:
        """후기 삭제"""
        # 후기 존재 및 작성자 확인
        review = await self.crud.get_review_by_id(review_id)
        if not review:
            raise ValueError("후기를 찾을 수 없습니다.")

        if review.user_id != user_id:
            raise ValueError("본인이 작성한 후기만 삭제할 수 있습니다.")

        return await self.crud.delete_review(review_id)

    async def get_review_stats_by_pod(self, pod_id: int) -> dict:
        """파티별 후기 통계 조회"""
        return await self.crud.get_review_stats_by_pod(pod_id)

    async def _convert_to_dto(self, review: PodReview) -> PodReviewDto:
        """PodReview 모델을 PodReviewDto로 변환"""
        try:
            logger.info(f"DTO 변환 시작: review_id={review.id}")

            # sub_categories 처리 (JSON 문자열을 리스트로 변환)
            sub_categories = review.pod.sub_categories
            if isinstance(sub_categories, str):
                import json

                sub_categories = json.loads(sub_categories)
            elif sub_categories is None:
                sub_categories = []

            logger.info(f"sub_categories 처리 완료: {sub_categories}")

            # SimplePodDto 생성
            simple_pod = SimplePodDto(
                id=review.pod.id,
                title=review.pod.title,
                image_url=review.pod.image_url,
                sub_categories=sub_categories,
            )

            logger.info(f"SimplePodDto 생성 완료: pod_id={simple_pod.id}")

        except Exception as e:
            logger.error(
                f"SimplePodDto 생성 중 오류: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise

        try:
            # SimpleUserDto 생성 (성향 정보는 별도로 조회)
            user_follow = SimpleUserDto(
                id=review.user.id,
                nickname=review.user.nickname,
                profile_image=review.user.profile_image,
                intro=review.user.intro,
                tendency_type=None,  # 필요시 별도 조회
                is_following=False,  # 필요시 별도 조회
            )

            logger.info(f"SimpleUserDto 생성 완료: user_id={user_follow.id}")

            result = PodReviewDto(
                id=review.id,
                pod=simple_pod,
                user=user_follow,
                rating=review.rating,
                content=review.content,
                created_at=review.created_at,
                updated_at=review.updated_at,
            )

            logger.info(f"PodReviewDto 생성 완료: review_id={result.id}")
            return result

        except Exception as e:
            logger.error(
                f"SimpleUserDto 또는 PodReviewDto 생성 중 오류: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise
