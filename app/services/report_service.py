from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.crud.user_report import UserReportCRUD
from app.crud.user import UserCRUD
from app.crud.user_block import UserBlockCRUD
from app.crud.follow import FollowCRUD
from app.schemas.report import ReportResponse, ReportReasonDto
from app.models.report_reason import ReportReason


class ReportService:
    """신고 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.report_crud = UserReportCRUD(db)
        self.user_crud = UserCRUD(db)
        self.block_crud = UserBlockCRUD(db)
        self.follow_crud = FollowCRUD(db)

    async def create_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        report_types: List[int],
        reason: Optional[str],
        should_block: bool,
    ) -> Optional[ReportResponse]:
        """사용자 신고 생성 (차단 옵션 포함)"""
        # 신고당한 사용자 존재 확인
        reported_user = await self.user_crud.get_by_id(reported_user_id)
        if not reported_user:
            return None

        # 신고 생성
        report = await self.report_crud.create_report(
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
            await self.block_crud.create_block(reporter_id, reported_user_id)

            # 팔로우 관계 삭제 (양방향)
            await self.follow_crud.delete_follow(reporter_id, reported_user_id)
            await self.follow_crud.delete_follow(reported_user_id, reporter_id)

        return ReportResponse(
            id=report.id,
            reporter_id=report.reporter_id,
            reported_user_id=report.reported_user_id,
            report_types=report.report_types,
            reason=report.reason,
            blocked=report.blocked,
            created_at=report.created_at,
        )

    @staticmethod
    def get_report_reasons() -> List[ReportReasonDto]:
        """신고 사유 목록 조회"""
        reasons = ReportReason.get_all_reasons()
        return [ReportReasonDto(**reason) for reason in reasons]
