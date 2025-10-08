from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import Optional, List
from datetime import datetime
from app.models.user_report import UserReport


class UserReportCRUD:
    """사용자 신고 CRUD 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        report_types: List[int],
        reason: Optional[str],
        blocked: bool,
    ) -> Optional[UserReport]:
        """사용자 신고 생성"""
        try:
            # 자기 자신을 신고하는지 확인
            if reporter_id == reported_user_id:
                return None

            report = UserReport(
                reporter_id=reporter_id,
                reported_user_id=reported_user_id,
                report_types=report_types,
                reason=reason,
                blocked=blocked,
            )
            self.db.add(report)
            await self.db.commit()
            await self.db.refresh(report)
            return report
        except Exception:
            await self.db.rollback()
            return None

    async def get_report_by_id(self, report_id: int) -> Optional[UserReport]:
        """신고 ID로 조회"""
        query = select(UserReport).where(UserReport.id == report_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_reports_by_reporter(
        self, reporter_id: int, page: int = 1, size: int = 20
    ) -> tuple[List[UserReport], int]:
        """신고자가 작성한 신고 목록 조회"""
        offset = (page - 1) * size

        query = (
            select(UserReport)
            .where(UserReport.reporter_id == reporter_id)
            .order_by(desc(UserReport.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        reports = result.scalars().all()

        # 총 개수 조회
        count_query = select(func.count(UserReport.id)).where(
            UserReport.reporter_id == reporter_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        return reports, total_count

    async def get_reports_by_reported_user(
        self, reported_user_id: int, page: int = 1, size: int = 20
    ) -> tuple[List[UserReport], int]:
        """신고당한 사용자의 신고 목록 조회"""
        offset = (page - 1) * size

        query = (
            select(UserReport)
            .where(UserReport.reported_user_id == reported_user_id)
            .order_by(desc(UserReport.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        reports = result.scalars().all()

        # 총 개수 조회
        count_query = select(func.count(UserReport.id)).where(
            UserReport.reported_user_id == reported_user_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        return reports, total_count
