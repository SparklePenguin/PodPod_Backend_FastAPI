from datetime import datetime, timezone

from app.features.pods.models import (
    Application,
    ApplicationStatus,
    Pod,
    PodMember,
)
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ApplicationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 파티 참여 신청서 생성
    async def create_application(
        self, pod_id: int, user_id: int, message: str | None = None
    ) -> Application:
        # 중복 신청 방지 (PENDING 상태만 체크)
        existing_application = await self._session.execute(
            select(Application).where(
                and_(
                    Application.pod_id == pod_id,
                    Application.user_id == user_id,
                    Application.status == ApplicationStatus.PENDING,
                )
            )
        )
        if existing_application.scalar_one_or_none() is not None:
            raise ValueError("이미 신청한 파티입니다.")

        # 현재 시간 저장
        current_time = datetime.now(timezone.utc)

        application = Application(
            pod_id=pod_id,
            user_id=user_id,
            message=message,
            status=ApplicationStatus.PENDING,
            applied_at=current_time,
        )
        self._session.add(application)
        await self._session.flush()
        await self._session.refresh(application)
        return application

    # - MARK: 신청서 조회 (상세)
    async def get_application_by_id(self, application_id: int) -> Application | None:
        result = await self._session.execute(
            select(Application).where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    # - MARK: 파티의 신청서 목록 조회 (리스트용)
    async def get_applications_by_pod_id(
        self,
        pod_id: int,
        status: str | ApplicationStatus | None = None,
        include_hidden: bool = False,
        current_user_id: int | None = None,
    ) -> list[Application]:
        query = select(Application).where(Application.pod_id == pod_id)

        if status:
            # status를 Enum으로 변환 (문자열인 경우)
            if isinstance(status, str):
                try:
                    status_enum = ApplicationStatus(status.lower())
                except ValueError:
                    status_enum = None
            else:
                status_enum = status
            if status_enum:
                query = query.where(Application.status == status_enum)

        # 숨김 처리된 신청서 제외 (기본값)
        if not include_hidden:
            query = query.where(~Application.is_hidden)

        # 차단된 유저의 신청서 필터링 제거 (모든 신청서 표시)

        query = query.order_by(Application.applied_at.desc())

        result = await self._session.execute(query)
        return list(result.scalars().all())

    # - MARK: 여러 파티의 신청서 목록 조회 (배치 로딩)
    async def get_applications_by_pod_ids(
        self,
        pod_ids: list[int],
        status: str | ApplicationStatus | None = None,
        include_hidden: bool = False,
    ) -> list[Application]:
        """여러 파티의 신청서를 한 번에 조회 (배치 로딩)"""
        if not pod_ids:
            return []

        query = select(Application).where(Application.pod_id.in_(pod_ids))

        if status:
            # status를 Enum으로 변환 (문자열인 경우)
            if isinstance(status, str):
                try:
                    status_enum = ApplicationStatus(status.lower())
                except ValueError:
                    status_enum = None
            else:
                status_enum = status
            if status_enum:
                query = query.where(Application.status == status_enum)

        # 숨김 처리된 신청서 제외 (기본값)
        if not include_hidden:
            query = query.where(~Application.is_hidden)

        query = query.order_by(Application.applied_at.desc())

        result = await self._session.execute(query)
        return list(result.scalars().all())

    # - MARK: 사용자의 신청서 목록 조회 (리스트용)
    async def get_applications_by_user_id(
        self, user_id: int, status: str | ApplicationStatus | None = None
    ) -> list[Application]:
        query = select(Application).where(Application.user_id == user_id)

        if status:
            # status를 Enum으로 변환 (문자열인 경우)
            if isinstance(status, str):
                try:
                    status_enum = ApplicationStatus(status.lower())
                except ValueError:
                    status_enum = None
            else:
                status_enum = status
            if status_enum:
                query = query.where(Application.status == status_enum)

        query = query.order_by(Application.applied_at.desc())

        result = await self._session.execute(query)
        return list(result.scalars().all())

    # - MARK: 신청서 승인/거절
    async def review_application(
        self, application_id: int, status: str | ApplicationStatus, reviewed_by: int
    ) -> Application:
        application = await self.get_application_by_id(application_id)
        if not application:
            raise ValueError("신청서를 찾을 수 없습니다.")

        application_status = getattr(application, "status", None)
        if application_status != ApplicationStatus.PENDING:
            raise ValueError("이미 처리된 신청서입니다.")

        # status를 Enum으로 변환 (문자열인 경우)
        if isinstance(status, str):
            try:
                status_enum = ApplicationStatus(status.lower())
            except ValueError:
                raise ValueError(f"유효하지 않은 상태값입니다: {status}")
        else:
            status_enum = status

        # 현재 시간 저장
        current_time = datetime.now(timezone.utc)

        application_db_id_raw = getattr(application, "id", None)
        application_db_id: int | None = None
        if application_db_id_raw is not None and isinstance(application_db_id_raw, int):
            application_db_id = application_db_id_raw
        if application_db_id is not None:
            stmt = (
                update(Application)
                .where(Application.id == application_db_id)
                .values(
                    status=status_enum,
                    reviewed_at=current_time,
                    reviewed_by=reviewed_by,
                )
            )
            await self._session.execute(stmt)
            await self._session.flush()
            await self._session.refresh(application)
        return application

    # - MARK: 신청서 삭제
    async def delete_application(self, application_id: int) -> bool:
        application = await self.get_application_by_id(application_id)
        if not application:
            return False

        await self._session.delete(application)
        await self._session.flush()
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
                update(Application)
                .where(Application.id == application_id_val)
                .values(is_hidden=True)
            )
            await self._session.execute(stmt)
            await self._session.flush()
            await self._session.refresh(application)
        return True

    # - MARK: 사용자의 모든 신청서 삭제
    async def delete_all_by_user_id(self, user_id: int) -> None:
        """사용자의 모든 파티 신청서 삭제"""
        from sqlalchemy import delete

        await self._session.execute(
            delete(Application).where(Application.user_id == user_id)
        )
        await self._session.flush()

    # - MARK: 파티 멤버 관리
    async def add_member(
        self,
        pod_id: int,
        user_id: int,
        role: str = "member",
        message: str | None = None,
    ) -> PodMember:
        """파티 멤버 추가"""
        # 중복 방지
        q = await self._session.execute(
            select(PodMember).where(
                PodMember.pod_id == pod_id, PodMember.user_id == user_id
            )
        )
        existing_member = q.scalar_one_or_none()
        if existing_member is not None:
            return existing_member

        # 파티 정보 조회 및 capacity 체크
        pod_q = await self._session.execute(
            select(Pod).where(Pod.id == pod_id, ~Pod.is_del)
        )
        pod = pod_q.scalar_one_or_none()
        if not pod:
            raise ValueError("파티를 찾을 수 없습니다")

        # 현재 멤버 수 확인
        member_count_q = await self._session.execute(
            select(func.count(PodMember.id)).where(PodMember.pod_id == pod_id)
        )
        current_member_count = member_count_q.scalar() or 0

        # capacity 체크 (owner는 이미 포함되어 있으므로 role이 member인 경우만 체크)
        pod_capacity = getattr(pod, "capacity", 0) or 0
        if role == "member" and current_member_count >= pod_capacity:
            raise ValueError("파티 정원이 가득 찼습니다")

        # 현재 시간을 datetime으로 저장
        current_datetime = datetime.now(timezone.utc)
        pod_member = PodMember(
            pod_id=pod_id,
            user_id=user_id,
            role=role,
            message=message,
            joined_at=current_datetime,
        )
        self._session.add(pod_member)

        await self._session.flush()
        await self._session.refresh(pod_member)
        return pod_member

    async def remove_member(self, pod_id: int, user_id: int) -> bool:
        """파티 멤버 제거"""
        q = await self._session.execute(
            select(PodMember).where(
                PodMember.pod_id == pod_id, PodMember.user_id == user_id
            )
        )
        row = q.scalar_one_or_none()
        if row is None:
            return True
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def list_members(self, pod_id: int) -> list[PodMember]:
        """파티 멤버 목록 조회"""
        q = await self._session.execute(
            select(PodMember)
            .options(selectinload(PodMember.user))
            .where(PodMember.pod_id == pod_id)
        )
        return list(q.scalars().all())
