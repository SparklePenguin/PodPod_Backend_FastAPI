from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.follow.repositories.follow_repository import FollowCRUD
from app.features.reports.models.report_reason import ReportReason
from app.features.reports.schemas import ReportReasonDto, ReportResponse
from app.features.users.repositories import (
    UserBlockRepository,
    UserReportRepository,
    UserRepository,
)


class ReportService:
    """신고 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._report_repo = UserReportRepository(db)
        self._user_repo = UserRepository(db)
        self._block_repo = UserBlockRepository(db)
        self._follow_repo = FollowCRUD(db)

    async def create_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        report_types: List[int],
        reason: str | None,
        should_block: bool,
    ) -> ReportResponse | None:
        """사용자 신고 생성 (차단 옵션 포함)"""
        # 신고당한 사용자 존재 확인
        reported_user = await self._user_repo.get_by_id(reported_user_id)
        if not reported_user:
            return None

        # 신고 생성
        report = await self._report_repo.create_report(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            report_types=report_types,
            reason=reason,
            blocked=should_block,
        )

        if not report:
            return None

        # 차단 여부에 따라 차단 처리
        if should_block:
            # 차단 생성
            await self._block_repo.create_block(reporter_id, reported_user_id)

            # 팔로우 관계 삭제 (양방향)
            await self._follow_repo.delete_follow(reporter_id, reported_user_id)
            await self._follow_repo.delete_follow(reported_user_id, reporter_id)

        report_id = getattr(report, "id", None) or 0
        report_reporter_id = getattr(report, "reporter_id", None) or 0
        report_reported_user_id = getattr(report, "reported_user_id", None) or 0
        report_report_types = getattr(report, "report_types", []) or []
        report_reason = getattr(report, "reason", None)
        report_blocked = bool(getattr(report, "blocked", False))
        report_created_at_raw = getattr(report, "created_at", None)

        # datetime 기본값 제공
        from datetime import datetime, timezone

        if report_created_at_raw is None:
            report_created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            report_created_at = report_created_at_raw

        return ReportResponse(
            id=report_id,
            reporter_id=report_reporter_id,
            reported_user_id=report_reported_user_id,
            report_types=report_report_types,
            reason=report_reason,
            blocked=report_blocked,
            created_at=report_created_at,
        )

    @staticmethod
    def get_report_reasons() -> List[ReportReasonDto]:
        """신고 사유 목록 조회"""
        reasons = ReportReason.get_all_reasons()
        return [ReportReasonDto(**reason) for reason in reasons]
