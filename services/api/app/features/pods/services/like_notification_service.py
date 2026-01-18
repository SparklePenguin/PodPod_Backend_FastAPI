"""Like 알림 서비스"""

from app.features.notifications.services.fcm_service import FCMService
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class LikeNotificationService:
    """Like 관련 알림을 처리하는 서비스"""

    def __init__(
        self,
        session: AsyncSession,
        fcm_service: FCMService,
        user_repo: UserRepository,
        pod_repo: PodRepository,
        like_repo: PodLikeRepository,
    ):
        self._session = session
        self._fcm_service = fcm_service
        self._user_repo = user_repo
        self._pod_repo = pod_repo
        self._like_repo = like_repo

    # MARK: - 좋아요 달성 알림
    async def send_likes_threshold_notification(self, pod_id: int) -> None:
        """좋아요 10개 달성 시 파티장에게 알림 전송"""
        try:
            # 현재 좋아요 수 확인
            like_count = await self._like_repo.like_count(pod_id)

            # 10개 달성 시에만 알림 전송
            if like_count == 10:
                # 파티 정보 조회
                pod = await self._pod_repo.get_pod_by_id(pod_id)
                if not pod:
                    return

                # 파티장 정보 조회
                if pod.owner_id is None:
                    return

                owner = await self._user_repo.get_by_id(pod.owner_id)

                if owner and owner.detail and owner.detail.fcm_token:
                    # 좋아요 달성 알림 전송
                    await self._fcm_service.send_pod_likes_threshold(
                        token=owner.detail.fcm_token,
                        party_name=pod.title or "",
                        pod_id=pod_id,
                        db=self._session,
                        user_id=owner.id,
                        related_user_id=pod.owner_id,
                    )
        except Exception:
            # 알림 전송 실패는 무시하고 계속 진행
            pass
