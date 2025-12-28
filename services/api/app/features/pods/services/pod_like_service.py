import logging

from app.core.services.fcm_service import FCMService
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.users.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PodLikeService:
    def __init__(self, session: AsyncSession, fcm_service: FCMService | None = None):
        self._session = session
        self.podLikeRepo = PodLikeRepository(session)
        self.pod_repo = PodRepository(session)
        self._fcm_service = fcm_service or FCMService()

    # - MARK: 좋아요 등록
    async def like_pod(self, pod_id: int, user_id: int) -> dict:
        ok = await self.podLikeRepo.like_pod(pod_id, user_id)

        # 좋아요 달성 알림 체크
        if ok:
            await self._check_likes_threshold(pod_id)

        return {"liked": ok}

    # - MARK: 좋아요 취소
    async def unlike_pod(self, pod_id: int, user_id: int) -> dict:
        ok = await self.podLikeRepo.unlike_pod(pod_id, user_id)
        return {"unliked": ok}

    # - MARK: 좋아요 상태
    async def like_status(self, pod_id: int, user_id: int) -> dict:
        return {
            "liked": await self.podLikeRepo.is_liked(pod_id, user_id),
            "count": await self.podLikeRepo.like_count(pod_id),
        }

    # - MARK: 좋아요 달성 알림 체크
    async def _check_likes_threshold(self, pod_id: int) -> None:
        """좋아요 10개 달성 시 파티장에게 알림 전송"""
        try:
            # 현재 좋아요 수 확인
            like_count = await self.podLikeRepo.like_count(pod_id)

            # 10개 달성 시에만 알림 전송
            if like_count == 10:
                # 파티 정보 조회
                pod = await self.pod_repo.get_pod_by_id(pod_id)
                if not pod:
                    return

                # 파티장 정보 조회
                if pod.owner_id is None:
                    return

                owner_result = await self._session.execute(
                    select(User).where(User.id == pod.owner_id)
                )
                owner = owner_result.scalar_one_or_none()

                if owner and owner.fcm_token:
                    # 좋아요 달성 알림 전송
                    await self._fcm_service.send_pod_likes_threshold(
                        token=owner.fcm_token,
                        party_name=pod.title or "",
                        pod_id=pod_id,
                        db=self._session,
                        user_id=owner.id,
                        related_user_id=pod.owner_id,
                    )
                    logger.info(
                        f"좋아요 10개 달성 알림 전송 성공: pod_id={pod_id}, owner_id={owner.id}"
                    )
                else:
                    logger.warning(
                        f"파티장 FCM 토큰이 없음: pod_id={pod_id}, owner_id={pod.owner_id}"
                    )

        except Exception as e:
            logger.error(f"좋아요 달성 알림 체크 실패: pod_id={pod_id}, error={e}")
