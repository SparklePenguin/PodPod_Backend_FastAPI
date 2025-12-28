from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse
from app.core.http_status import HttpStatus
from app.deps.auth import get_current_user_id
from app.deps.database import get_session
from app.features.reports.schemas import (
    CreateReportRequest,
    ReportReasonsResponse,
    ReportResponse,
)
from app.features.reports.services.report_service import ReportService

router = APIRouter()


@router.get(
    "/reasons",
    response_model=BaseResponse[ReportReasonsResponse],
    description="신고 사유 목록 조회",
)
async def get_report_reasons(db: AsyncSession = Depends(get_session)):
    report_service = ReportService(db)
    reasons = report_service.get_report_reasons()

    return BaseResponse.ok(
        data=ReportReasonsResponse(reasons=reasons),
        http_status=HttpStatus.OK,
        message_ko="신고 사유 목록을 조회했습니다.",
        message_en="Successfully retrieved report reasons.",
    )


@router.post(
    "/",
    response_model=BaseResponse[ReportResponse],
    description="사용자 신고 생성 (차단 옵션 포함)",
)
async def create_report(
    request: CreateReportRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    from app.features.users.exceptions import UserNotFoundException

    # 자기 자신을 신고하려는 경우
    if request.reported_user_id == current_user_id:
        from app.core.exceptions import DomainException
        from fastapi.responses import JSONResponse

        from app.common.schemas import BaseResponse

        exc = DomainException(error_key="CANNOT_REPORT_SELF")
        response = BaseResponse(
            data=None,
            error_key=exc.error_code,
            error_code=exc.error_code_num,
            http_status=exc.status_code,
            message_ko=exc.message_ko,
            message_en=exc.message_en,
            dev_note=exc.dev_note,
        )
        return JSONResponse(
            status_code=exc.status_code, content=response.model_dump(by_alias=True)
        )

    report_service = ReportService(db)
    report = await report_service.create_report(
        reporter_id=current_user_id,
        reported_user_id=request.reported_user_id,
        report_types=request.report_types,
        reason=request.reason,
        should_block=request.should_block,
    )

    if not report:
        raise UserNotFoundException(request.reported_user_id)

    message_ko = "신고가 접수되었습니다."
    message_en = "Report submitted successfully."

    if request.should_block:
        message_ko += " 해당 사용자가 차단되었으며 팔로우 관계도 해제되었습니다."
        message_en += " The user has been blocked and follow relationship removed."

    return BaseResponse.ok(
        data=report,
        http_status=HttpStatus.CREATED,
        message_ko=message_ko,
        message_en=message_en,
    )
