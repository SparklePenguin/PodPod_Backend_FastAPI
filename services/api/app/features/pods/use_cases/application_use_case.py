"""Application Use Case - 비즈니스 로직 처리"""

from typing import List, cast

from app.features.pods.exceptions import (
    AlreadyAppliedException,
    AlreadyMemberException,
    NoPodAccessPermissionException,
    PodAlreadyClosedException,
    PodIsFullException,
    PodNotFoundException,
)
from app.features.pods.repositories.application_repository import (
    ApplicationRepository,
)
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.schemas.application_schemas import PodApplDto
from app.features.pods.services.application_dto_service import ApplicationDtoService
from app.features.pods.services.application_notification_service import (
    ApplicationNotificationService,
)
from app.features.users.exceptions import UserNotFoundException
from app.features.users.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class ApplicationUseCase:
    """Application 관련 비즈니스 로직을 처리하는 Use Case"""

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
        self._dto_service = ApplicationDtoService(session, user_repo)

    # MARK: - 파티 참여 신청
    async def apply_to_pod(
        self, pod_id: int, user_id: int, message: str | None = None
    ) -> PodApplDto:
        """파티 참여 신청"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        if pod.owner_id is None:
            raise PodNotFoundException(pod_id)

        # 이미 멤버인지 확인
        pod_members = await self._application_repo.list_members(pod_id)
        already_member = any(m.user_id == user_id for m in pod_members)
        if already_member:
            raise AlreadyMemberException(pod_id, user_id)

        # 신청서 생성
        try:
            application = await self._application_repo.create_application(
                pod_id, user_id, message
            )

            # User 정보 가져오기
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundException(user_id)

            # 파티장에게 알림 전송
            if pod.owner_id:
                await self._notification_service.send_pod_join_request_notification(
                    pod_id=pod_id,
                    owner_id=pod.owner_id,
                    applicant_id=user_id,
                    applicant_nickname=user.nickname or "",
                )

            await self._session.commit()

            # DTO 변환
            return await self._dto_service.convert_to_dto(application)
        except ValueError as e:
            if "이미 신청한 파티입니다" in str(e):
                await self._session.rollback()
                raise AlreadyAppliedException(pod_id, user_id)
            await self._session.rollback()
            raise e
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 신청서 승인/거절
    async def review_application(
        self, application_id: int, status: str, reviewed_by: int
    ) -> PodApplDto:
        """신청서 승인/거절 처리"""
        # 신청서 존재 확인
        application = await self._application_repo.get_application_by_id(application_id)
        if not application:
            raise PodNotFoundException(0)

        try:
            # 신청서 상태 업데이트
            application = await self._application_repo.review_application(
                application_id, status, reviewed_by
            )

            application_pod_id = application.pod_id or 0
            application_user_id = application.user_id or 0

            # 승인된 경우 처리
            if status.lower() == "approved":
                # 정원 확인
                pod = await self._pod_repo.get_pod_by_id(application_pod_id)
                if not pod:
                    await self._session.rollback()
                    raise PodNotFoundException(application_pod_id)

                member_count = await self._pod_repo.get_joined_users_count(
                    application_pod_id
                )
                if member_count >= (pod.capacity or 0):
                    await self._session.rollback()
                    raise PodIsFullException(application_pod_id)

                # 멤버로 추가
                application_message_str = (
                    str(application.message)
                    if application.message is not None
                    else None
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

                # 채팅방에 멤버 추가
                await self._add_member_to_chat_room(
                    application_pod_id, application_user_id
                )

            # 신청자에게 알림 전송
            user = await self._user_repo.get_by_id(application_user_id)
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
                    await self._check_and_send_capacity_full_notification(
                        application_pod_id
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

            await self._session.commit()

            # DTO 변환
            reviewer_dto = await self._dto_service.create_reviewer_dto(reviewed_by)
            return await self._dto_service.convert_to_dto(application, reviewer_dto)
        except PodIsFullException:
            await self._session.rollback()
            raise
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 신청서 숨김 처리
    async def hide_application(self, application_id: int, user_id: int) -> bool:
        """파티장이 신청서를 숨김 처리"""
        # 신청서 조회
        application = await self._application_repo.get_application_by_id(application_id)
        if not application:
            raise PodNotFoundException(0)

        # 파티 조회
        if application.pod_id is None:
            raise PodNotFoundException(0)
        if not isinstance(application.pod_id, int):
            raise PodNotFoundException(0)
        application_pod_id = cast(int, application.pod_id)
        pod = await self._pod_repo.get_pod_by_id(application_pod_id)
        if not pod:
            raise PodNotFoundException(application_pod_id)

        # 파티장 권한 확인
        if pod.owner_id != user_id:
            raise NoPodAccessPermissionException(application_pod_id, user_id)

        # 숨김 처리
        try:
            result = await self._application_repo.hide_application(application_id)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 신청서 취소
    async def cancel_application(self, application_id: int, user_id: int) -> bool:
        """신청자가 신청서를 취소"""
        # 신청서 조회
        application = await self._application_repo.get_application_by_id(application_id)
        if not application:
            raise PodNotFoundException(0)

        # 신청자 권한 확인
        if application.user_id != user_id:
            if application.pod_id is None:
                raise NoPodAccessPermissionException(0, user_id)
            if not isinstance(application.pod_id, int):
                raise NoPodAccessPermissionException(0, user_id)
            application_pod_id = cast(int, application.pod_id)
            raise NoPodAccessPermissionException(application_pod_id, user_id)

        # pending 상태만 취소 가능
        application_status = application.status
        if application_status != "pending":
            if application.pod_id is None:
                raise PodAlreadyClosedException(0)
            if not isinstance(application.pod_id, int):
                raise PodAlreadyClosedException(0)
            application_pod_id = cast(int, application.pod_id)
            raise PodAlreadyClosedException(application_pod_id)

        # 취소 처리
        try:
            result = await self._application_repo.delete_application(application_id)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티별 신청서 목록 조회
    async def get_applications_by_pod_id(
        self, pod_id: int, include_hidden: bool = False
    ) -> List[PodApplDto]:
        """파티별 신청서 목록 조회"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        applications = await self._application_repo.get_applications_by_pod_id(
            pod_id, include_hidden=include_hidden
        )

        # DTO 변환
        return [
            await self._dto_service.convert_to_list_dto(app, include_message=False)
            for app in applications
        ]

    # MARK: - Private 헬퍼 메서드
    async def _add_member_to_chat_room(self, pod_id: int, user_id: int) -> None:
        """채팅방에 멤버 추가"""
        try:
            from app.features.chat.repositories.chat_room_repository import (
                ChatRoomRepository,
            )

            pod = await self._pod_repo.get_pod_by_id(pod_id)
            if pod and pod.chat_room_id:
                chat_room_repo = ChatRoomRepository(self._session)
                await chat_room_repo.add_member(
                    chat_room_id=pod.chat_room_id,
                    user_id=user_id,
                    role="member",
                )

                # Redis 캐시에도 멤버 추가
                try:
                    from app.deps.redis import get_redis_client
                    from app.features.chat.services.chat_redis_cache_service import (
                        ChatRedisCacheService,
                    )

                    redis = await get_redis_client()
                    redis_cache = ChatRedisCacheService(redis)
                    await redis_cache.add_member(pod.chat_room_id, user_id)
                except Exception:
                    pass  # Redis 실패해도 DB는 성공했으므로 무시
        except Exception:
            pass

    async def _check_and_send_capacity_full_notification(self, pod_id: int) -> None:
        """정원 가득 참 알림 전송"""
        from app.features.pods.models.pod import PodStatus

        final_pod = await self._pod_repo.get_pod_by_id(pod_id)
        if final_pod:
            final_member_count = await self._pod_repo.get_joined_users_count(pod_id)
            final_pod_capacity = final_pod.capacity or 0
            final_pod_status = final_pod.status
            if (
                final_member_count >= final_pod_capacity
                or final_pod_status == PodStatus.COMPLETED
            ):
                await self._notification_service.send_capacity_full_notification(
                    pod_id, final_pod
                )
