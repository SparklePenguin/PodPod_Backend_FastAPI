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
from app.features.pods.schemas import PodApplDto
from app.features.pods.services.application_service import ApplicationService
from sqlalchemy.ext.asyncio import AsyncSession


class ApplicationUseCase:
    """Application 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        application_service: ApplicationService,
        pod_repo: PodRepository,
        application_repo: ApplicationRepository,
    ):
        self._session = session
        self._application_service = application_service
        self._pod_repo = pod_repo
        self._application_repo = application_repo

    # MARK: - 파티 참여 신청
    async def apply_to_pod(
        self, pod_id: int, user_id: int, message: str | None = None
    ) -> PodApplDto:
        """파티 참여 신청 (비즈니스 로직 검증)"""
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

        # 신청서 생성 (서비스 로직 호출)
        try:
            result = await self._application_service.create_application(
                pod_id, user_id, message
            )
            await self._session.commit()
            return result
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
        """신청서 승인/거절 (비즈니스 로직 검증)"""
        # 신청서 존재 확인
        application = await self._application_repo.get_application_by_id(application_id)
        if not application:
            raise PodNotFoundException(0)

        # 서비스 로직 호출
        try:
            result = await self._application_service.review_application(
                application_id, status, reviewed_by
            )

            # 승인 시 정원 확인 (추가 비즈니스 검증)
            if status.lower() == "approved":
                if application.pod_id is None:
                    await self._session.rollback()
                    raise PodNotFoundException(0)

                pod = await self._pod_repo.get_pod_by_id(application.pod_id)
                if not pod:
                    await self._session.rollback()
                    raise PodNotFoundException(application.pod_id)

                # 정원 확인
                try:
                    member_count = await self._pod_repo.get_joined_users_count(
                        application.pod_id
                    )
                    if member_count >= (pod.capacity or 0):
                        await self._session.rollback()
                        raise PodIsFullException(application.pod_id)
                except PodIsFullException:
                    await self._session.rollback()
                    raise
                except Exception:
                    # 정원 확인 실패는 무시 (서비스에서 이미 처리)
                    pass

            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 신청서 숨김 처리
    async def hide_application(self, application_id: int, user_id: int) -> bool:
        """파티장이 신청서를 숨김 처리 (권한 검증)"""
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

        # 서비스 로직 호출
        try:
            result = await self._application_service.hide_application(
                application_id, user_id
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 신청서 취소
    async def cancel_application(self, application_id: int, user_id: int) -> bool:
        """신청자가 신청서를 취소 (권한 및 상태 검증)"""
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

        # 서비스 로직 호출
        try:
            result = await self._application_service.cancel_application(
                application_id, user_id
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티별 신청서 목록 조회
    async def get_applications_by_pod_id(
        self, pod_id: int, include_hidden: bool = False
    ) -> List[PodApplDto]:
        """파티별 신청서 목록 조회 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 서비스 로직 호출
        return await self._application_service.get_applications_by_pod_id(
            pod_id, include_hidden
        )
