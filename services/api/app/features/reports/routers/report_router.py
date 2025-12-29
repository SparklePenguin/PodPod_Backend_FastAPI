from typing import List

from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.service import get_report_service
from app.features.reports.schemas import (
    CreateReportRequest,
    ReportInfoDto,
    ReportReasonDto,
)
from app.features.reports.services.report_service import ReportService
from fastapi import APIRouter, Depends

router = APIRouter()


# - MARK: 신고 사유 목록 조회
@router.get(
    "/reasons",
    response_model=BaseResponse[List[ReportReasonDto]],
    description="신고 사유 목록 조회",
)
async def get_report_reasons(
    service: ReportService = Depends(get_report_service),
):
    result = service.get_report_reasons()
    return BaseResponse.ok(data=result)


# - MARK: 신고 생성
@router.post(
    "/",
    response_model=BaseResponse[ReportInfoDto],
    description="사용자 신고 생성 (차단 옵션 포함)",
)
async def create_report(
    request: CreateReportRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: ReportService = Depends(get_report_service),
):
    result = await service.create_report(
        reporter_id=current_user_id,
        reported_user_id=request.reported_user_id,
        report_types=request.report_types,
        reason=request.reason,
        should_block=request.should_block,
    )
    return BaseResponse.ok(data=result)
