from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.pods.models.pod.pod import Pod
from app.features.pods.models.pod.pod_member import PodMember
from app.features.pods.models.pod_review import PodReview


class PodReviewCRUD:
    """파티 후기 CRUD 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review(
        self, pod_id: int, user_id: int, rating: int, content: str
    ) -> Optional[PodReview]:
        """후기 생성"""
        review = PodReview(
            pod_id=pod_id,
            user_id=user_id,
            rating=rating,
            content=content,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)

        # 관계 로딩을 위해 다시 조회
        review_id = getattr(review, "id", None)
        if review_id is None:
            return None
        return await self.get_review_by_id(review_id)

    async def get_review_by_id(self, review_id: int) -> Optional[PodReview]:
        """ID로 후기 조회"""
        query = (
            select(PodReview)
            .options(selectinload(PodReview.pod), selectinload(PodReview.user))
            .where(PodReview.id == review_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_review_by_pod_and_user(
        self, pod_id: int, user_id: int
    ) -> Optional[PodReview]:
        """파티와 사용자로 후기 조회"""
        query = (
            select(PodReview)
            .options(selectinload(PodReview.pod), selectinload(PodReview.user))
            .where(and_(PodReview.pod_id == pod_id, PodReview.user_id == user_id))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_reviews_by_pod(
        self, pod_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[PodReview], int]:
        """특정 파티의 후기 목록 조회"""
        offset = (page - 1) * size

        # 후기 목록 조회 (파티, 사용자, 성향 정보 포함)
        query = (
            select(PodReview)
            .options(selectinload(PodReview.pod), selectinload(PodReview.user))
            .where(PodReview.pod_id == pod_id)
            .order_by(desc(PodReview.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        # 총 후기 수 조회
        count_query = select(func.count(PodReview.id)).where(PodReview.pod_id == pod_id)
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        return reviews, total_count

    async def get_all_reviews_by_pod(self, pod_id: int) -> List[PodReview]:
        """특정 파티의 모든 후기 목록 조회 (페이지네이션 없음)"""
        query = (
            select(PodReview)
            .options(selectinload(PodReview.pod), selectinload(PodReview.user))
            .where(PodReview.pod_id == pod_id)
            .order_by(desc(PodReview.created_at))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_reviews_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[PodReview], int]:
        """특정 사용자가 작성한 후기 목록 조회"""
        offset = (page - 1) * size

        # 후기 목록 조회 (파티, 사용자, 성향 정보 포함)
        query = (
            select(PodReview)
            .options(selectinload(PodReview.pod), selectinload(PodReview.user))
            .where(PodReview.user_id == user_id)
            .order_by(desc(PodReview.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        # 총 후기 수 조회
        count_query = select(func.count(PodReview.id)).where(
            PodReview.user_id == user_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        return reviews, total_count

    async def update_review(
        self, review_id: int, rating: int, content: str
    ) -> Optional[PodReview]:
        """후기 수정"""
        query = select(PodReview).where(PodReview.id == review_id)
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()

        if review:
            stmt = (
                update(PodReview)
                .where(PodReview.id == review_id)
                .values(rating=rating, content=content)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(review)
            return review
        return None

    async def delete_review(self, review_id: int) -> bool:
        """후기 삭제"""
        query = select(PodReview).where(PodReview.id == review_id)
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()

        if review:
            await self.db.delete(review)
            await self.db.commit()
            return True
        return False

    async def get_review_stats_by_pod(self, pod_id: int) -> dict:
        """파티별 후기 통계 조회"""
        # 평균 별점
        avg_rating_query = select(func.avg(PodReview.rating)).where(
            PodReview.pod_id == pod_id
        )
        avg_rating_result = await self.db.execute(avg_rating_query)
        avg_rating = avg_rating_result.scalar() or 0

        # 총 후기 수
        total_reviews_query = select(func.count(PodReview.id)).where(
            PodReview.pod_id == pod_id
        )
        total_reviews_result = await self.db.execute(total_reviews_query)
        total_reviews = total_reviews_result.scalar() or 0

        return {
            "avg_rating": round(avg_rating, 1),
            "total_reviews": total_reviews,
        }

    async def get_reviews_received_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[PodReview], int]:
        """특정 사용자가 참여한 파티에 대한 받은 리뷰 목록 조회 (본인이 작성한 리뷰 제외)"""
        offset = (page - 1) * size

        # 내가 참여한 파티 ID 목록 조회
        # 1. PodMember로 참여한 파티
        member_pods_query = select(PodMember.pod_id).where(PodMember.user_id == user_id)
        member_pods_result = await self.db.execute(member_pods_query)
        member_pod_ids = [row[0] for row in member_pods_result.all()]

        # 2. 내가 개설한 파티 (owner_id)
        owner_pods_query = select(Pod.id).where(Pod.owner_id == user_id)
        owner_pods_result = await self.db.execute(owner_pods_query)
        owner_pod_ids = [row[0] for row in owner_pods_result.all()]

        # 참여한 모든 파티 ID 합치기
        all_pod_ids = list(set(member_pod_ids + owner_pod_ids))

        if not all_pod_ids:
            # 참여한 파티가 없으면 빈 리스트 반환
            return [], 0

        # 해당 파티들에 대한 리뷰 중에서 내가 작성하지 않은 리뷰들 조회
        query = (
            select(PodReview)
            .options(selectinload(PodReview.pod), selectinload(PodReview.user))
            .where(
                and_(
                    PodReview.pod_id.in_(all_pod_ids),
                    PodReview.user_id != user_id,  # 내가 작성하지 않은 리뷰
                )
            )
            .order_by(desc(PodReview.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        # 총 리뷰 수 조회
        count_query = select(func.count(PodReview.id)).where(
            and_(
                PodReview.pod_id.in_(all_pod_ids),
                PodReview.user_id != user_id,
            )
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        return reviews, total_count
