from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user_id
from app.services.report_service import ReportService
from app.schemas.report import (
    CreateReportRequest,
    ReportResponse,
    ReportReasonDto,
    ReportReasonsResponse,
)
from app.schemas.common.base_response import BaseResponse
from app.core.http_status import HttpStatus
from app.core.error_codes import get_error_info
from typing import List

router = APIRouter()


@router.get("/reasons", response_model=BaseResponse[ReportReasonsResponse])
async def get_report_reasons():
    """신고 사유 목록 조회"""
    try:
        report_service = ReportService(None)  # DB 불필요
        reasons = report_service.get_report_reasons()

        return BaseResponse.ok(
            data=ReportReasonsResponse(reasons=reasons),
            http_status=HttpStatus.OK,
            message_ko="신고 사유 목록을 조회했습니다.",
            message_en="Successfully retrieved report reasons.",
        )
    except Exception as e:
        import traceback

        print(f"신고 사유 목록 조회 오류: {e}")
        traceback.print_exc()
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="신고 사유 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving report reasons.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.post("/", response_model=BaseResponse[ReportResponse])
async def create_report(
    request: CreateReportRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """사용자 신고 생성 (차단 옵션 포함)"""
    try:
        # 자기 자신을 신고하려는 경우
        if request.reported_user_id == current_user_id:
            return BaseResponse(
                data=None,
                http_status=400,
                message_ko="자기 자신을 신고할 수 없습니다.",
                message_en="Cannot report yourself.",
                error="CANNOT_REPORT_SELF",
                error_code=4010,
                dev_note=None,
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
            return BaseResponse(
                data=None,
                http_status=404,
                message_ko="신고할 사용자를 찾을 수 없습니다.",
                message_en="User to report not found.",
                error="USER_NOT_FOUND",
                error_code=4004,
                dev_note=None,
            )

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
    except ValueError as e:
        return BaseResponse(
            data=None,
            http_status=400,
            message_ko=str(e),
            message_en="Invalid report request.",
            error="INVALID_REPORT_REQUEST",
            error_code=4011,
            dev_note=None,
        )
    except Exception as e:
        import traceback

        print(f"신고 생성 오류: {e}")
        traceback.print_exc()
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="신고 접수 중 오류가 발생했습니다.",
            message_en="An error occurred while submitting the report.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )
