"""Review 알림 서비스"""

from app.core.services.fcm_service import FCMService
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class ReviewNotificationService:
    """Review 관련 알림을 처리하는 서비스"""

    def __init__(
        self,
        session: AsyncSession,
        fcm_service: FCMService,
        user_repo: UserRepository,
        pod_repo: PodRepository,
    ):
        self._session = session
        self._fcm_service = fcm_service
        self._user_repo = user_repo
        self._pod_repo = pod_repo

    # MARK: - 리뷰 생성 알림
    async def send_review_created_notification(
        self, review_id: int, pod_id: int, reviewer_id: int
    ) -> None:
        """리뷰 생성 시 파티 참여자들에게 알림 전송"""
        try:
            # 리뷰 작성자 정보 조회
            reviewer = await self._user_repo.get_by_id(reviewer_id)

            # 파티 정보 조회
            pod = await self._pod_repo.get_pod_by_id(pod_id)
            if not pod:
                return

            if not reviewer:
                return

            # 파티장 정보 조회
            owner = (
                await self._user_repo.get_by_id(pod.owner_id) if pod.owner_id else None
            )

            if not owner:
                return

            # 파티장에게만 알림 전송 (리뷰 작성자가 파티장이 아닌 경우)
            if owner.id is not None and owner.id != reviewer_id:
                try:
                    if owner.fcm_token:
                        await self._fcm_service.send_review_created(
                            token=owner.fcm_token,
                            nickname=reviewer.nickname or "",
                            party_name=pod.title or "",
                            review_id=review_id,
                            db=self._session,
                            user_id=owner.id,
                            related_user_id=reviewer_id,  # 리뷰 작성자
                            related_pod_id=pod_id,  # 리뷰를 남긴 파티
                        )
                except Exception:
                    pass

            # 리뷰 작성자 제외 참여자들에게 REVIEW_OTHERS_CREATED 알림 전송
            participants = await self._pod_repo.get_pod_participants(pod_id)
            reviewer_nickname = reviewer.nickname or ""
            for participant in participants:
                # 리뷰 작성자 제외
                if participant.id is not None and participant.id == reviewer_id:
                    continue
                # 파티장은 이미 REVIEW_CREATED를 받았으므로 제외
                if (
                    participant.id is not None
                    and pod.owner_id is not None
                    and participant.id == pod.owner_id
                ):
                    continue

                try:
                    if participant.fcm_token:
                        await self._fcm_service.send_review_others_created(
                            token=participant.fcm_token,
                            nickname=reviewer_nickname,
                            review_id=review_id,
                            pod_id=pod_id,
                            db=self._session,
                            user_id=participant.id,
                            related_user_id=reviewer_id,
                        )
                except Exception:
                    pass

        except Exception:
            # 알림 전송 실패는 무시하고 계속 진행
            pass
