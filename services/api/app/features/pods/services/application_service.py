"""Application Service - 서비스 로직만 처리 (데이터 접근, DTO 변환, 알림 전송)"""

from typing import List

from app.core.services.sendbird_service import SendbirdService
from app.features.pods.models import ApplicationDetail, PodStatus
from app.features.pods.repositories.application_repository import (
    ApplicationRepository,
)
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.schemas import PodApplDetailDto, PodApplDto
from app.features.pods.services.application_notification_service import (
    ApplicationNotificationService,
)
from app.features.users.exceptions import UserNotFoundException
from app.features.users.models import User
from app.features.users.repositories import UserRepository
from app.features.users.schemas import UserDto
from sqlalchemy.ext.asyncio import AsyncSession


class ApplicationService:
    """Pod 신청서 관련 서비스 로직을 처리하는 서비스 (데이터 접근, DTO 변환, 알림 전송)"""

    def __init__(
        self,
        session: AsyncSession,
        pod_repo: PodRepository,
        application_repo: ApplicationRepository,
        user_repo: UserRepository,
        notification_service: ApplicationNotificationService,
    ):
        self._session = session
        self._pod_repo = pod_repo
        self._application_repo = application_repo
        self._user_repo = user_repo
        self._notification_service = notification_service

    # MARK: - 헬퍼 메서드
    def _create_user_dto(self, user: User | None, tendency_type: str = "") -> UserDto:
        """User 모델과 성향 타입으로 UserDto 생성"""
        if not user:
            return UserDto(
                id=0,
                nickname="",
                profile_image="",
                intro="",
                tendency_type=tendency_type,
                is_following=False,
            )

        return UserDto(
            id=user.id or 0,
            nickname=user.nickname or "",
            profile_image=user.profile_image or "",
            intro=user.intro or "",
            tendency_type=tendency_type,
            is_following=False,
        )

    def _create_pod_appl_dto(
        self,
        application: ApplicationDetail,
        user_dto: UserDto,
        include_message: bool = True,
    ) -> PodApplDto:
        """Application 모델과 UserDto로 PodApplDto 생성 (리스트용)"""
        message = None
        if include_message:
            message = getattr(application, "message", None)
        
        status_str = str(application.status) if application.status else ""
        if not status_str and hasattr(application, "status"):
            status_str = str(application.status) if application.status else ""
        
        return PodApplDto(
            id=application.id or 0,
            user=user_dto,
            status=status_str,
            message=message,
            applied_at=application.applied_at,
        )

    def _create_application_dto(
        self,
        application: ApplicationDetail,
        user_dto: UserDto,
        reviewer_dto: UserDto | None = None,
    ) -> PodApplDetailDto:
        """Application 모델과 UserDto로 PodApplDetailDto 생성"""
        return PodApplDetailDto(
            id=application.id or 0,
            podId=application.pod_id or 0,
            user=user_dto,
            message=application.message,
            status=str(application.status) if application.status else "",
            appliedAt=application.applied_at,
            reviewedAt=application.reviewed_at,
            reviewedBy=reviewer_dto,
        )

    # MARK: - 신청서 생성
    async def create_application(
        self, pod_id: int, user_id: int, message: str | None = None
    ) -> PodApplDetailDto:
        """신청서 생성 및 DTO 변환 (서비스 로직)"""
        # 신청서 생성
        application = await self._application_repo.create_application(
            pod_id, user_id, message
        )

        # User 정보 가져오기
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)

        # 성향 타입 조회
        tendency_type = await self._user_repo.get_user_tendency_type(user_id)

        # 파티 정보 조회 (알림 전송용)
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod and pod.owner_id:
            await self._notification_service.send_pod_join_request_notification(
                pod_id=pod_id,
                owner_id=pod.owner_id,
                applicant_id=user_id,
                applicant_nickname=user.nickname or "",
            )

        # DTO 변환
        user_dto = self._create_user_dto(user, tendency_type)
        return self._create_application_dto(application, user_dto, reviewer_dto=None)

    # MARK: - 신청서 승인/거절 처리
    async def review_application(
        self, application_id: int, status: str, reviewed_by: int
    ) -> PodApplDetailDto:
        """신청서 승인/거절 처리 및 DTO 변환 (서비스 로직)"""
        # 신청서 승인/거절 처리
        application = await self._application_repo.review_application(
            application_id, status, reviewed_by
        )

        application_pod_id = application.pod_id or 0
        application_user_id = application.user_id or 0

        # 승인된 경우 멤버로 추가
        if status.lower() == "approved":
            application_message_str = (
                str(application.message) if application.message is not None else None
            )
            await self._application_repo.add_member(
                application_pod_id,
                application_user_id,
                role="member",
                message=application_message_str,
            )

            # 세션 캐시 무효화
            self._session.expire_all()

            # 새 멤버 참여 알림 전송
            await self._notification_service.send_new_member_notification(
                application_pod_id, application_user_id
            )

            # 샌드버드 채팅방에 멤버 초대
            try:
                pod = await self._pod_repo.get_pod_by_id(application_pod_id)
                if pod and pod.chat_channel_url:
                    sendbird_service = SendbirdService()
                    await sendbird_service.join_channel(
                        channel_url=pod.chat_channel_url,
                        user_ids=[str(application_user_id)],
                    )
            except Exception:
                pass

        # User 정보 가져오기
        user = await self._user_repo.get_by_id(application_user_id)
        reviewer = await self._user_repo.get_by_id(reviewed_by) if reviewed_by else None

        # 신청자에게 FCM 알림 전송
        if user:
            pod = await self._pod_repo.get_pod_by_id(application_pod_id)
            pod_title = pod.title or "" if pod else "파티"

            if status.lower() == "approved":
                await self._notification_service.send_pod_request_approved_notification(
                    user_id=user.id,
                    pod_id=application_pod_id,
                    pod_title=pod_title,
                    reviewed_by=reviewed_by,
                )

                # 정원 가득 참 알림 전송
                final_pod = await self._pod_repo.get_pod_by_id(application_pod_id)
                if final_pod:
                    final_member_count = await self._pod_repo.get_joined_users_count(
                        application_pod_id
                    )
                    final_pod_capacity = final_pod.capacity or 0
                    final_pod_status = final_pod.status
                    if (
                        final_member_count >= final_pod_capacity
                        or final_pod_status == PodStatus.COMPLETED
                    ):
                        await (
                            self._notification_service.send_capacity_full_notification(
                                application_pod_id, final_pod
                            )
                        )
            elif status.lower() == "rejected":
                await self._notification_service.send_pod_request_rejected_notification(
                    user_id=user.id,
                    pod_id=application_pod_id,
                    pod_title=pod_title,
                    reviewed_by=reviewed_by,
                )

                # 좋아요한 파티에 자리 생김 알림 전송
                await self._notification_service.send_spot_opened_notifications(
                    application_pod_id, pod
                )

        # 성향 타입 조회
        user_tendency_type = await self._user_repo.get_user_tendency_type(
            application_user_id
        )
        reviewer_tendency_type = ""
        if reviewer:
            reviewer_tendency_type = await self._user_repo.get_user_tendency_type(
                reviewed_by
            )

        # DTO 변환
        user_dto = self._create_user_dto(user, user_tendency_type)

        reviewer_dto = None
        if reviewer and reviewer.id is not None:
            reviewer_dto = self._create_user_dto(reviewer, reviewer_tendency_type)

        return self._create_application_dto(application, user_dto, reviewer_dto)

    # MARK: - 파티별 신청서 목록 조회
    async def get_applications_by_pod_id(
        self, pod_id: int, include_hidden: bool = False
    ) -> List[PodApplDto]:
        """파티별 신청서 목록 조회 및 DTO 변환 (서비스 로직) - 리스트용"""
        applications = await self._application_repo.get_applications_by_pod_id(
            pod_id, include_hidden=include_hidden
        )

        # DTO 변환 (리스트용 - 간단한 정보만)
        application_dtos = []
        for application in applications:
            user_id_value = application.user_id
            user = await self._user_repo.get_by_id(user_id_value)

            # 성향 타입 조회
            user_tendency_type = await self._user_repo.get_user_tendency_type(
                user_id_value
            )

            # UserDto 생성
            user_dto = self._create_user_dto(user, user_tendency_type or "")

            # PodApplDto 생성 (리스트용 - 간단한 정보만)
            application_dto = self._create_pod_appl_dto(
                application, user_dto, include_message=False
            )
            application_dtos.append(application_dto)

        return application_dtos

    # MARK: - 신청서 숨김 처리
    async def hide_application(self, application_id: int, user_id: int) -> bool:
        """신청서 숨김 처리 (서비스 로직)"""
        result = await self._application_repo.hide_application(application_id)
        return result

    # MARK: - 신청서 취소
    async def cancel_application(self, application_id: int, user_id: int) -> bool:
        """신청서 취소 (서비스 로직)"""
        result = await self._application_repo.delete_application(application_id)
        return result
