from typing import List

from app.features.users.models import UserReport
from sqlalchemy.ext.asyncio import AsyncSession


class UserReportRepository:
    """사용자 신고 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 신고 생성 (커밋 없음)
    async def create_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        report_types: List[int],
        reason: str | None,
        blocked: bool,
    ) -> UserReport | None:
        """사용자 신고 생성 (커밋은 use_case에서 처리)"""
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
            self._session.add(report)
            return report
        except Exception:
            await self._session.rollback()
            return None
