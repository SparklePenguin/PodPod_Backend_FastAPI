from typing import List

from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.reports.exceptions import CannotReportSelfException
from app.features.reports.models.report_reason import ReportReason
from app.features.reports.schemas import ReportInfoDto, ReportReasonDto
from app.features.users.exceptions import UserNotFoundException
from app.features.users.repositories import (
    BlockUserRepository,
    UserReportRepository,
    UserRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession


class ReportService:
    """신고 서비스 클래스"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._report_repo = UserReportRepository(session)
        self._user_repo = UserRepository(session)
        self._block_repo = BlockUserRepository(session)
        self._follow_repo = FollowRepository(session)

    # - MARK: 신고 생성
    async def create_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        report_types: List[int],
        reason: str | None,
        should_block: bool,
    ) -> ReportInfoDto:
        """사용자 신고 생성 (차단 옵션 포함)"""
        # 자기 자신을 신고하려는 경우
        if reporter_id == reported_user_id:
            raise CannotReportSelfException()

        # 신고당한 사용자 존재 확인
        reported_user = await self._user_repo.get_by_id(reported_user_id)
        if not reported_user:
            raise UserNotFoundException(reported_user_id)

        # 신고 생성
        report = await self._report_repo.create_report(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            report_types=report_types,
            reason=reason,
            blocked=should_block,
        )

        if not report:
            raise UserNotFoundException(reported_user_id)

        # 차단 여부에 따라 차단 처리
        if should_block:
            # 차단 생성
            await self._block_repo.create_block(reporter_id, reported_user_id)

            # 팔로우 관계 삭제 (양방향)
            await self._follow_repo.delete_follow(reporter_id, reported_user_id)
            await self._follow_repo.delete_follow(reported_user_id, reporter_id)

        return ReportInfoDto(
            id=report.id,
            reporter_id=report.reporter_id,
            reported_user_id=report.reported_user_id,
            report_types=report.report_types or [],
            reason=report.reason,
            blocked=bool(report.blocked),
            created_at=report.created_at,
        )

    # - MARK: 신고 사유 목록 조회
    @staticmethod
    def get_report_reasons() -> List[ReportReasonDto]:
        """신고 사유 목록 조회"""
        reasons = ReportReason.get_all_reasons()
        return [ReportReasonDto(**reason) for reason in reasons]
