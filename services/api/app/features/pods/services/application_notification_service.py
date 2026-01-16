"""Application 알림 서비스"""

from app.features.notifications.services.fcm_service import FCMService
from app.features.pods.models import Pod
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.users.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class ApplicationNotificationService:
    """Application 관련 알림을 처리하는 서비스"""

    def __init__(
        self,
        session: AsyncSession,
        fcm_service: FCMService,
        user_repo: UserRepository,
        pod_repo: PodRepository,
        like_repo: PodLikeRepository,
    ):
        self._session = session
        self._user_repo = user_repo
        self._fcm_service = fcm_service
        self._pod_repo = pod_repo
        self._like_repo = like_repo

    # MARK: - 파티 참여 신청 알림
    async def send_pod_join_request_notification(
        self, pod_id: int, owner_id: int, applicant_id: int, applicant_nickname: str
    ) -> None:
        """파티장에게 파티 참여 신청 알림 전송"""
        try:
            # 파티장 정보 조회
            owner = await self._user_repo.get_by_id(owner_id)
            if not owner or not owner.detail or not owner.detail.fcm_token:
                return

            await self._fcm_service.send_pod_join_request(
                token=owner.detail.fcm_token,
                nickname=applicant_nickname,
                pod_id=pod_id,
                db=self._session,
                user_id=owner.id,
                related_user_id=applicant_id,
            )
        except Exception:
            # 알림 전송 실패는 무시하고 계속 진행
            pass

    # MARK: - 신청서 승인 알림
    async def send_pod_request_approved_notification(
        self,
        user_id: int,
        pod_id: int,
        pod_title: str,
        reviewed_by: int,
    ) -> None:
        """신청자에게 신청서 승인 알림 전송"""
        try:
            user = await self._user_repo.get_by_id(user_id)
            if not user or not user.detail or not user.detail.fcm_token:
                return

            await self._fcm_service.send_pod_request_approved(
                token=user.detail.fcm_token,
                party_name=pod_title,
                pod_id=pod_id,
                db=self._session,
                user_id=user.id,
                related_user_id=reviewed_by,
                related_pod_id=pod_id,
            )
        except Exception:
            pass

    # MARK: - 신청서 거절 알림
    async def send_pod_request_rejected_notification(
        self,
        user_id: int,
        pod_id: int,
        pod_title: str,
        reviewed_by: int,
    ) -> None:
        """신청자에게 신청서 거절 알림 전송"""
        try:
            user = await self._user_repo.get_by_id(user_id)
            if not user or not user.detail or not user.detail.fcm_token:
                return

            await self._fcm_service.send_pod_request_rejected(
                token=user.detail.fcm_token,
                party_name=pod_title,
                pod_id=pod_id,
                db=self._session,
                user_id=user.id,
                related_user_id=reviewed_by,
                related_pod_id=pod_id,
            )
        except Exception:
            pass

    # MARK: - 정원 가득 참 알림
    async def send_capacity_full_notification(self, pod_id: int, pod: Pod) -> None:
        """파티 정원이 가득 찬 경우 파티장에게 알림 전송"""
        try:
            if pod.owner_id is None:
                return

            owner = await self._user_repo.get_by_id(pod.owner_id)
            if not owner or not owner.detail or not owner.detail.fcm_token:
                return

            await self._fcm_service.send_pod_capacity_full(
                token=owner.detail.fcm_token,
                party_name=pod.title or "",
                pod_id=pod_id,
                db=self._session,
                user_id=owner.id,
                related_user_id=pod.owner_id,
            )
        except Exception:
            pass

    # MARK: - 새 멤버 참여 알림
    async def send_new_member_notification(
        self, pod_id: int, new_member_id: int
    ) -> None:
        """새 멤버 참여 시 파티장, 신청자 제외 참여 유저에게 알림 전송"""
        try:
            pod = await self._pod_repo.get_pod_by_id(pod_id)
            if not pod:
                return

            new_member = await self._user_repo.get_by_id(new_member_id)
            if not new_member:
                return

            participants = await self._pod_repo.get_pod_participants(pod_id)
            new_member_nickname = new_member.nickname or ""
            pod_title = pod.title or ""

            for participant in participants:
                if (
                    participant.id is not None
                    and pod.owner_id is not None
                    and participant.id == pod.owner_id
                ):
                    continue
                if participant.id == new_member_id:
                    continue

                try:
                    if participant.detail and participant.detail.fcm_token and participant.id:
                        await self._fcm_service.send_pod_new_member(
                            token=participant.detail.fcm_token,
                            nickname=new_member_nickname,
                            party_name=pod_title,
                            pod_id=pod_id,
                            db=self._session,
                            user_id=participant.id,
                            related_user_id=new_member_id,
                        )
                except Exception:
                    pass
        except Exception:
            pass

    # MARK: - 좋아요한 파티에 자리 생김 알림
    async def send_spot_opened_notifications(self, pod_id: int, pod: Pod | None) -> None:
        """파티에 자리가 생겼을 때 좋아요한 사용자들에게 알림 전송"""
        try:
            if not pod:
                return

            liked_users = await self._like_repo.get_users_who_liked_pod(pod_id)
            if not liked_users:
                return

            for user in liked_users:
                try:
                    if user.detail and user.detail.fcm_token:
                        await self._fcm_service.send_saved_pod_spot_opened(
                            token=user.detail.fcm_token,
                            party_name=pod.title or "",
                            pod_id=pod_id,
                            db=self._session,
                            user_id=user.id,
                            related_user_id=pod.owner_id,
                        )
                except Exception:
                    pass
        except Exception:
            pass
