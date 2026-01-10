"""Pod 알림 서비스"""

from app.core.services.fcm_service import FCMService
from app.features.pods.models import Pod, PodStatus
from app.features.pods.repositories.pod_repository import PodRepository
from sqlalchemy.ext.asyncio import AsyncSession


class PodNotificationService:
    """Pod 관련 알림을 처리하는 서비스"""

    def __init__(
        self,
        session: AsyncSession,
        fcm_service: FCMService,
        pod_repo: PodRepository,
    ):
        self._session = session
        self._fcm_service = fcm_service
        self._pod_repo = pod_repo

    # MARK: - 파티 수정 알림
    async def send_pod_update_notification(self, pod_id: int, pod: Pod) -> None:
        """파티 수정 알림 전송"""
        try:
            participants = await self._pod_repo.get_pod_participants(pod_id)

            for participant in participants:
                if (
                    participant.id is not None
                    and pod.owner_id is not None
                    and participant.id != pod.owner_id
                    and participant.detail
                    and participant.detail.fcm_token
                ):
                    try:
                        await self._fcm_service.send_pod_updated(
                            token=participant.detail.fcm_token,
                            party_name=pod.title or "",
                            pod_id=pod_id,
                            db=self._session,
                            user_id=participant.id,
                            related_user_id=pod.owner_id,
                        )
                    except Exception:
                        # 알림 전송 실패는 무시하고 계속 진행
                        pass
        except Exception:
            # 알림 전송 실패는 무시하고 계속 진행
            pass

    # MARK: - 파티 상태 업데이트 알림
    async def send_pod_status_update_notification(
        self, pod_id: int, pod: Pod, status: PodStatus
    ) -> None:
        """파티 상태 업데이트 알림 전송"""
        try:
            participants = await self._pod_repo.get_pod_participants(pod_id)

            # 상태별 알림 전송
            if status == PodStatus.COMPLETED:
                # 파티 확정 알림 (모집 완료) - 파티장 제외 참여자에게 전송
                for participant in participants:
                    # 파티장 제외
                    if (
                        participant.id is not None
                        and pod.owner_id is not None
                        and participant.id == pod.owner_id
                    ):
                        continue
                    try:
                        if participant.detail and participant.detail.fcm_token:
                            await self._fcm_service.send_pod_confirmed(
                                token=participant.detail.fcm_token,
                                party_name=pod.title or "",
                                pod_id=pod_id,
                                db=self._session,
                                user_id=participant.id,
                                related_user_id=pod.owner_id,
                            )
                    except Exception:
                        pass

            elif status == PodStatus.CANCELED:
                # 파티 취소 알림 - 파티장 제외 참여자에게 전송
                for participant in participants:
                    # 파티장 제외
                    if (
                        participant.id is not None
                        and pod.owner_id is not None
                        and participant.id == pod.owner_id
                    ):
                        continue
                    try:
                        if participant.detail and participant.detail.fcm_token:
                            await self._fcm_service.send_pod_canceled(
                                token=participant.detail.fcm_token,
                                party_name=pod.title or "",
                                pod_id=pod_id,
                                db=self._session,
                                user_id=participant.id,
                                related_user_id=pod.owner_id,
                            )
                    except Exception:
                        pass

            elif status == PodStatus.CLOSED:
                # 파티 완료 알림
                for participant in participants:
                    try:
                        if (
                            participant.detail
                            and participant.detail.fcm_token
                            and participant.id is not None
                        ):
                            await self._fcm_service.send_pod_completed(
                                token=participant.detail.fcm_token,
                                party_name=pod.title or "",
                                pod_id=pod_id,
                                db=self._session,
                                user_id=participant.id,
                                related_user_id=pod.owner_id,
                            )
                    except Exception:
                        pass

        except Exception:
            # 알림 전송 실패는 무시하고 계속 진행
            pass
