from sqlalchemy.ext.asyncio import AsyncSession
from app.features.pods.repositories.like_repository import PodLikeCRUD
from app.features.pods.repositories.pod_repository import PodCRUD
from app.core.services.fcm_service import FCMService
from sqlalchemy import select
from app.features.pods.models.pod import Pod
from app.features.users.models import User
import logging

logger = logging.getLogger(__name__)


class PodLikeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = PodLikeCRUD(db)
        self.pod_crud = PodCRUD(db)

    # - MARK: 좋아요 등록
    async def like_pod(self, pod_id: int, user_id: int) -> dict:
        ok = await self.crud.like_pod(pod_id, user_id)

        # 좋아요 달성 알림 체크
        if ok:
            await self._check_likes_threshold(pod_id)

        return {"liked": ok}

    # - MARK: 좋아요 취소
    async def unlike_pod(self, pod_id: int, user_id: int) -> dict:
        ok = await self.crud.unlike_pod(pod_id, user_id)
        return {"unliked": ok}

    # - MARK: 좋아요 상태
    async def like_status(self, pod_id: int, user_id: int) -> dict:
        return {
            "liked": await self.crud.is_liked(pod_id, user_id),
            "count": await self.crud.like_count(pod_id),
        }

    # - MARK: 좋아요 달성 알림 체크
    async def _check_likes_threshold(self, pod_id: int) -> None:
        """좋아요 10개 달성 시 파티장에게 알림 전송"""
        try:
            # 현재 좋아요 수 확인
            like_count = await self.crud.like_count(pod_id)

            # 10개 달성 시에만 알림 전송
            if like_count == 10:
                # 파티 정보 조회
                pod = await self.pod_crud.get_pod_by_id(pod_id)
                if not pod:
                    return

                # 파티장 정보 조회
                pod_owner_id = getattr(pod, "owner_id", None)
                if pod_owner_id is None:
                    return

                owner_result = await self.db.execute(
                    select(User).where(User.id == pod_owner_id)
                )
                owner = owner_result.scalar_one_or_none()

                owner_fcm_token = getattr(owner, "fcm_token", None) if owner else None
                if owner and owner_fcm_token:
                    # FCM 서비스 초기화
                    fcm_service = FCMService()

                    # 좋아요 달성 알림 전송
                    owner_id = getattr(owner, "id", None)
                    pod_title = getattr(pod, "title", "") or ""
                    await fcm_service.send_pod_likes_threshold(
                        token=owner_fcm_token,
                        party_name=pod_title,
                        pod_id=pod_id,
                        db=self.db,
                        user_id=owner_id,
                        related_user_id=pod_owner_id,
                    )
                    logger.info(
                        f"좋아요 10개 달성 알림 전송 성공: pod_id={pod_id}, owner_id={owner_id}"
                    )
                else:
                    logger.warning(
                        f"파티장 FCM 토큰이 없음: pod_id={pod_id}, owner_id={pod_owner_id}"
                    )

        except Exception as e:
            logger.error(f"좋아요 달성 알림 체크 실패: pod_id={pod_id}, error={e}")
