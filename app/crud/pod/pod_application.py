from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.pod import PodApplication
from app.models.pod.pod_application import ApplicationStatus
from datetime import datetime, timezone


class PodApplicationCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: 파티 참여 신청서 생성
    async def create_application(
        self, pod_id: int, user_id: int, message: str = None
    ) -> PodApplication:
        # 중복 신청 방지 (PENDING 상태만 체크)
        existing_application = await self.db.execute(
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
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        return application

    # - MARK: 신청서 조회
    async def get_application_by_id(self, application_id: int) -> PodApplication:
        result = await self.db.execute(
            select(PodApplication).where(PodApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    # - MARK: 파티의 신청서 목록 조회
    async def get_applications_by_pod_id(
        self,
        pod_id: int,
        status: str = None,
        include_hidden: bool = False,
        current_user_id: int = None,
    ) -> list[PodApplication]:
        query = select(PodApplication).where(PodApplication.pod_id == pod_id)

        if status:
            query = query.where(PodApplication.status == status)

        # 숨김 처리된 신청서 제외 (기본값)
        if not include_hidden:
            query = query.where(PodApplication.is_hidden == False)

        # 차단된 유저의 신청서 필터링 제거 (모든 신청서 표시)

        query = query.order_by(PodApplication.applied_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    # - MARK: 사용자의 신청서 목록 조회
    async def get_applications_by_user_id(
        self, user_id: int, status: str = None
    ) -> list[PodApplication]:
        query = select(PodApplication).where(PodApplication.user_id == user_id)

        if status:
            query = query.where(PodApplication.status == status)

        query = query.order_by(PodApplication.applied_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    # - MARK: 신청서 승인/거절
    async def review_application(
        self, application_id: int, status: str, reviewed_by: int
    ) -> PodApplication:
        application = await self.get_application_by_id(application_id)
        if not application:
            raise ValueError("신청서를 찾을 수 없습니다.")

        if application.status != ApplicationStatus.PENDING:
            raise ValueError("이미 처리된 신청서입니다.")

        # 현재 시간을 Unix timestamp로 저장
        current_timestamp = int(datetime.now(timezone.utc).timestamp())

        application.status = status
        application.reviewed_at = current_timestamp
        application.reviewed_by = reviewed_by

        await self.db.commit()
        await self.db.refresh(application)
        return application

    # - MARK: 신청서 삭제
    async def delete_application(self, application_id: int) -> bool:
        application = await self.get_application_by_id(application_id)
        if not application:
            return False

        await self.db.delete(application)
        await self.db.commit()
        return True

    # - MARK: 신청서 숨김 처리
    async def hide_application(self, application_id: int) -> bool:
        """파티장이 신청서를 숨김 처리"""
        application = await self.get_application_by_id(application_id)
        if not application:
            return False

        application.is_hidden = True
        await self.db.commit()
        await self.db.refresh(application)
        return True

    # - MARK: 사용자의 모든 신청서 삭제
    async def delete_all_by_user_id(self, user_id: int) -> None:
        """사용자의 모든 파티 신청서 삭제"""
        from sqlalchemy import delete

        await self.db.execute(
            delete(PodApplication).where(PodApplication.user_id == user_id)
        )
        await self.db.commit()
