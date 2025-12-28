"""
에러 코드 관리 엔드포인트 (관리자용)
"""

import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.common.schemas import BaseResponse
from app.core.config import settings
from app.core.error_codes import (
    get_cached_error_codes,
    load_error_codes_from_file,
    load_error_codes_from_sheets,
)
from app.core.http_status import HttpStatus

router = APIRouter(prefix="/admin/error-codes", tags=["admin-error-codes"])


@router.get(
    "/",
    response_model=BaseResponse[Dict[str, Any]],
    summary="에러 코드 목록 조회",
    description="현재 로드된 모든 에러 코드를 조회합니다.",
)
async def get_error_codes():
    """현재 로드된 에러 코드 목록을 반환합니다."""
    try:
        error_codes = get_cached_error_codes()
        return BaseResponse.ok(
            data={"error_codes": error_codes, "total_count": len(error_codes)},
            http_status=HttpStatus.OK,
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"에러 코드 조회 실패: {str(e)}",
        )


@router.post(
    "/reload-from-sheets",
    response_model=BaseResponse[Dict[str, Any]],
    summary="Google Sheets에서 에러 코드 다시 로드",
    description="Google Sheets에서 에러 코드를 다시 로드합니다.",
)
async def reload_from_sheets(
    spreadsheet_id: str | None = None, range_name: str | None = None
):
    """Google Sheets에서 에러 코드를 다시 로드합니다."""
    try:
        # 파라미터가 없으면 설정에서 가져오기
        if not spreadsheet_id:
            spreadsheet_id = settings.GOOGLE_SHEETS_ID

        if not range_name:
            range_name = settings.GOOGLE_SHEETS_RANGE

        if not spreadsheet_id:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="Google Sheets ID가 설정되지 않았습니다.",
            )

        success = await load_error_codes_from_sheets(
            spreadsheet_id=spreadsheet_id, range_name=range_name, force_reload=True
        )

        if success:
            error_codes = get_cached_error_codes()
            return BaseResponse.ok(
                data={
                    "message": "Google Sheets에서 에러 코드를 성공적으로 로드했습니다.",
                    "total_count": len(error_codes),
                },
                http_status=HttpStatus.OK,
            )
        else:
            raise HTTPException(
                status_code=HttpStatus.INTERNAL_SERVER_ERROR,
                detail="Google Sheets에서 에러 코드 로드에 실패했습니다.",
            )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"에러 코드 로드 실패: {str(e)}",
        )


@router.post(
    "/reload-from-file",
    response_model=BaseResponse[Dict[str, Any]],
    summary="로컬 파일에서 에러 코드 다시 로드",
    description="로컬 JSON 파일에서 에러 코드를 다시 로드합니다.",
)
async def reload_from_file(file_path: str = "error_codes_backup.json"):
    """로컬 파일에서 에러 코드를 다시 로드합니다."""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"파일을 찾을 수 없습니다: {file_path}",
            )

        success = load_error_codes_from_file(file_path)

        if success:
            error_codes = get_cached_error_codes()
            return BaseResponse.ok(
                data={
                    "message": f"로컬 파일에서 에러 코드를 성공적으로 로드했습니다: {file_path}",
                    "total_count": len(error_codes),
                },
                http_status=HttpStatus.OK,
            )
        else:
            raise HTTPException(
                status_code=HttpStatus.INTERNAL_SERVER_ERROR,
                detail="로컬 파일에서 에러 코드 로드에 실패했습니다.",
            )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"에러 코드 로드 실패: {str(e)}",
        )


@router.get(
    "/validate",
    response_model=BaseResponse[Dict[str, Any]],
    summary="에러 코드 유효성 검증",
    description="현재 로드된 에러 코드들의 유효성을 검증합니다.",
)
async def validate_error_codes():
    """에러 코드의 유효성을 검증합니다."""
    try:
        from app.core.services.google_sheets_service import google_sheets_service

        error_codes = get_cached_error_codes()
        validation_errors = google_sheets_service.validate_error_codes(error_codes)

        return BaseResponse.ok(
            data={
                "is_valid": len(validation_errors) == 0,
                "validation_errors": validation_errors,
                "total_count": len(error_codes),
            },
            http_status=HttpStatus.OK,
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"에러 코드 검증 실패: {str(e)}",
        )


@router.get(
    "/sheets",
    response_model=BaseResponse[Dict[str, Any]],
    summary="Google Sheets 시트 목록 조회",
    description="Google Sheets에서 사용 가능한 시트 목록을 조회합니다.",
)
async def get_sheets_list():
    """Google Sheets에서 시트 목록을 가져옵니다."""
    try:
        from app.core.services.google_sheets_service import google_sheets_service

        if not settings.GOOGLE_SHEETS_ID:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="Google Sheets ID가 설정되지 않았습니다.",
            )

        # Google Sheets 서비스 초기화
        await google_sheets_service.initialize(settings.GOOGLE_SHEETS_ID, "Sheet1!A:A")

        # 서비스가 초기화되었는지 확인
        if not google_sheets_service.service:
            raise HTTPException(
                status_code=HttpStatus.INTERNAL_SERVER_ERROR,
                detail="Google Sheets 서비스 초기화에 실패했습니다.",
            )

        # 시트 목록 가져오기
        result = (
            google_sheets_service.service.spreadsheets()
            .get(spreadsheetId=settings.GOOGLE_SHEETS_ID)
            .execute()
        )

        sheets = []
        for sheet in result.get("sheets", []):
            sheet_properties = sheet.get("properties", {})
            sheets.append(
                {
                    "title": sheet_properties.get("title", ""),
                    "sheet_id": sheet_properties.get("sheetId", 0),
                    "index": sheet_properties.get("index", 0),
                }
            )

        return BaseResponse.ok(
            data={"sheets": sheets, "total_count": len(sheets)},
            http_status=HttpStatus.OK,
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"시트 목록 조회 실패: {str(e)}",
        )


@router.get(
    "/info",
    response_model=BaseResponse[Dict[str, Any]],
    summary="에러 코드 시스템 정보",
    description="에러 코드 시스템의 현재 상태와 설정 정보를 조회합니다.",
)
async def get_error_codes_info():
    """에러 코드 시스템 정보를 반환합니다."""
    try:
        error_codes = get_cached_error_codes()

        # 카테고리별 개수 계산
        categories = {
            "1xxx": 0,  # 인증/로그인
            "2xxx": 0,  # 회원가입/프로필
            "3xxx": 0,  # 결제/정산
            "4xxx": 0,  # 데이터/리소스
            "5xxx": 0,  # 서버/시스템
        }

        for error_key, error_data in error_codes.items():
            code = error_data.get("code", 0)
            if 1000 <= code < 2000:
                categories["1xxx"] += 1
            elif 2000 <= code < 3000:
                categories["2xxx"] += 1
            elif 3000 <= code < 4000:
                categories["3xxx"] += 1
            elif 4000 <= code < 5000:
                categories["4xxx"] += 1
            elif 5000 <= code < 6000:
                categories["5xxx"] += 1

        return BaseResponse.ok(
            data={
                "total_count": len(error_codes),
                "categories": categories,
                "google_sheets_id": settings.GOOGLE_SHEETS_ID,
                "google_sheets_range": settings.GOOGLE_SHEETS_RANGE,
                "backup_file_exists": os.path.exists("error_codes_backup.json"),
            },
            http_status=HttpStatus.OK,
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"에러 코드 정보 조회 실패: {str(e)}",
        )
