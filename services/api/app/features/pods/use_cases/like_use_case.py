"""Like Use Case - 비즈니스 로직 처리"""

from app.features.pods.exceptions import PodNotFoundException
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.services.like_service import LikeService
from sqlalchemy.ext.asyncio import AsyncSession


class LikeUseCase:
    """Like 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        like_service: LikeService,
        pod_repo: PodRepository,
        like_repo: PodLikeRepository,
    ):
        self._session = session
        self._like_service = like_service
        self._pod_repo = pod_repo
        self._like_repo = like_repo

    # MARK: - 좋아요 등록
    async def like_pod(self, pod_id: int, user_id: int) -> dict:
        """파티 좋아요 등록 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        # 서비스 로직 호출
        try:
            result = await self._like_service.like_pod(pod_id, user_id)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 좋아요 취소
    async def unlike_pod(self, pod_id: int, user_id: int) -> dict:
        """파티 좋아요 취소 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        # 서비스 로직 호출
        try:
            result = await self._like_service.unlike_pod(pod_id, user_id)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 좋아요 상태 조회
    async def like_status(self, pod_id: int, user_id: int) -> dict:
        """파티 좋아요 상태 조회 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        # 서비스 로직 호출
        return await self._like_service.like_status(pod_id, user_id)
