"""Like Use Case - 비즈니스 로직 처리"""

from app.features.pods.exceptions import PodNotFoundException
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.services.like_notification_service import (
    LikeNotificationService,
)
from sqlalchemy.ext.asyncio import AsyncSession


class LikeUseCase:
    """Like 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        like_repo: PodLikeRepository,
        pod_repo: PodRepository,
        notification_service: LikeNotificationService,
    ):
        self._session = session
        self._like_repo = like_repo
        self._pod_repo = pod_repo
        self._notification_service = notification_service

    # MARK: - 좋아요 등록
    async def like_pod(self, pod_id: int, user_id: int) -> dict:
        """파티 좋아요 등록"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        # 좋아요 등록
        ok = await self._like_repo.like_pod(pod_id, user_id)
        await self._session.commit()

        # 좋아요 달성 알림 체크
        if ok:
            await self._notification_service.send_likes_threshold_notification(pod_id)

        return {"liked": ok}

    # MARK: - 좋아요 취소
    async def unlike_pod(self, pod_id: int, user_id: int) -> dict:
        """파티 좋아요 취소"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        # 좋아요 취소
        ok = await self._like_repo.unlike_pod(pod_id, user_id)
        await self._session.commit()

        return {"unliked": ok}

    # MARK: - 좋아요 상태 조회
    async def like_status(self, pod_id: int, user_id: int) -> dict:
        """파티 좋아요 상태 조회"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        return {
            "liked": await self._like_repo.is_liked(pod_id, user_id),
            "count": await self._like_repo.like_count(pod_id),
        }
