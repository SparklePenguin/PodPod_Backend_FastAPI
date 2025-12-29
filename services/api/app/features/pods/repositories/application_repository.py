from datetime import datetime, timezone

from app.features.pods.models.pod import PodApplication
from app.features.pods.models.pod.pod_application import ApplicationStatus
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class PodApplicationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 파티 참여 신청서 생성
    async def create_application(
        self, pod_id: int, user_id: int, message: str | None = None
    ) -> PodApplication:
        # 중복 신청 방지 (PENDING 상태만 체크)
        existing_application = await self._session.execute(
            select(PodApplication).where(
                and_(
                    PodApplication.pod_id == pod_id,
                    PodApplication.user_id == user_id,
                    PodApplication.status == ApplicationStatus.PENDING,
                )
            )
        )
        if existing_application.scalar_one_or_none() is not None:
            raise ValueError("이미 신청한 파티입니다.")

        # 현재 시간을 Unix timestamp로 저장
        current_timestamp = int(datetime.now(timezone.utc).timestamp())

        application = PodApplication(
            pod_id=pod_id,
            user_id=user_id,
            message=message,
            status=ApplicationStatus.PENDING,
            applied_at=current_timestamp,
        )
        self._session.add(application)
        await self._session.commit()
        await self._session.refresh(application)
        return application

    # - MARK: 신청서 조회
    async def get_application_by_id(self, application_id: int) -> PodApplication:
        result = await self._session.execute(
            select(PodApplication).where(PodApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    # - MARK: 파티의 신청서 목록 조회
    async def get_applications_by_pod_id(
        self,
        pod_id: int,
        status: str | None = None,
        include_hidden: bool = False,
        current_user_id: int | None = None,
    ) -> list[PodApplication]:
        query = select(PodApplication).where(PodApplication.pod_id == pod_id)

        if status:
            query = query.where(PodApplication.status == status)

        # 숨김 처리된 신청서 제외 (기본값)
        if not include_hidden:
            query = query.where(~PodApplication.is_hidden)

        # 차단된 유저의 신청서 필터링 제거 (모든 신청서 표시)

        query = query.order_by(PodApplication.applied_at.desc())

        result = await self._session.execute(query)
        return list(result.scalars().all())

    # - MARK: 사용자의 신청서 목록 조회
    async def get_applications_by_user_id(
        self, user_id: int, status: str | None = None
    ) -> list[PodApplication]:
        query = select(PodApplication).where(PodApplication.user_id == user_id)

        if status:
            query = query.where(PodApplication.status == status)

        query = query.order_by(PodApplication.applied_at.desc())

        result = await self._session.execute(query)
        return list(result.scalars().all())

    # - MARK: 신청서 승인/거절
    async def review_application(
        self, application_id: int, status: str, reviewed_by: int
    ) -> PodApplication:
        application = await self.get_application_by_id(application_id)
        if not application:
            raise ValueError("신청서를 찾을 수 없습니다.")

        application_status = getattr(application, "status", None)
        if application_status != ApplicationStatus.PENDING:
            raise ValueError("이미 처리된 신청서입니다.")

        # 현재 시간을 Unix timestamp로 저장
        current_timestamp = int(datetime.now(timezone.utc).timestamp())

        application_db_id_raw = getattr(application, "id", None)
        application_db_id: int | None = None
        if application_db_id_raw is not None and isinstance(application_db_id_raw, int):
            application_db_id = application_db_id_raw
        if application_db_id is not None:
            stmt = (
                update(PodApplication)
                .where(PodApplication.id == application_db_id)
                .values(
                    status=status,
                    reviewed_at=current_timestamp,
                    reviewed_by=reviewed_by,
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            await self._session.refresh(application)
        return application

    # - MARK: 신청서 삭제
    async def delete_application(self, application_id: int) -> bool:
        application = await self.get_application_by_id(application_id)
        if not application:
            return False

        await self._session.delete(application)
        await self._session.commit()
        return True

    # - MARK: 신청서 숨김 처리
    async def hide_application(self, application_id: int) -> bool:
        """파티장이 신청서를 숨김 처리"""
        application = await self.get_application_by_id(application_id)
        if not application:
            return False

        application_id_val = getattr(application, "id", None)
        if application_id_val is not None:
            stmt = (
                update(PodApplication)
                .where(PodApplication.id == application_id_val)
                .values(is_hidden=True)
            )
            await self._session.execute(stmt)
            await self._session.commit()
            await self._session.refresh(application)
        return True

    # - MARK: 사용자의 모든 신청서 삭제
    async def delete_all_by_user_id(self, user_id: int) -> None:
        """사용자의 모든 파티 신청서 삭제"""
        from sqlalchemy import delete

        await self._session.execute(
            delete(PodApplication).where(PodApplication.user_id == user_id)
        )
        await self._session.commit()
