"""
PodPod Backend API 에러 코드 체계

에러 코드 분류:
- 1xxx: 인증/로그인 관련 오류
- 2xxx: 회원 가입/프로필 관련 오류
- 3xxx: 결제/정산 관련 오류
- 4xxx: 데이터/리소스 접근 관련 오류
- 5xxx: 서버/시스템 관련 오류
"""

from typing import Dict, Any
from fastapi import HTTPException
from app.core.http_status import HttpStatus
import os
import json
import asyncio
from functools import lru_cache
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class ErrorInfo:
    """에러 정보를 담는 객체"""

    error_key: str
    code: int
    message_ko: str
    message_en: str
    http_status: int
    dev_note: str = None

    @property
    def message(self) -> str:
        """기본 메시지 (한국어)"""
        return self.message_ko

    def get_message(self, language: str = "ko") -> str:
        """언어에 따른 메시지 반환"""
        if language == "en":
            return self.message_en
        return self.message_ko


# 에러 코드 정의 (JSON 파일에서 로드됨)
ERROR_CODES: Dict[str, Dict[str, Any]] = {}

# 캐시 파일 경로
CACHE_FILE = "error_codes_backup.json"
CACHE_DURATION_HOURS = 24


def _is_cache_valid() -> bool:
    """캐시 파일이 유효한지 확인합니다 (24시간 이내)."""
    if not os.path.exists(CACHE_FILE):
        return False

    try:
        file_time = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        return datetime.now() - file_time < timedelta(hours=CACHE_DURATION_HOURS)
    except Exception:
        return False


def _load_from_cache() -> bool:
    """캐시 파일에서 에러 코드를 로드합니다."""
    global ERROR_CODES

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            ERROR_CODES = json.load(f)
        print(f"캐시 파일에서 {len(ERROR_CODES)}개의 에러 코드를 로드했습니다.")
        return True
    except Exception as e:
        print(f"캐시 파일 로드 실패: {str(e)}")
        return False


async def load_error_codes_from_sheets(
    spreadsheet_id: str,
    range_name: str = None,  # 더 이상 사용하지 않음
    force_reload: bool = False,
) -> bool:
    """
    Google Sheets에서 에러 코드를 로드합니다.
    캐시가 유효하면 캐시를 사용하고, 그렇지 않으면 Google Sheets에서 새로 로드합니다.

    Args:
        spreadsheet_id: Google Sheets 스프레드시트 ID
        range_name: 시트 범위 (기본값: "Sheet1!A:F")
        force_reload: 강제로 새로 로드할지 여부

    Returns:
        성공 여부
    """
    global ERROR_CODES

    # 강제 리로드가 아니고 캐시가 유효하면 캐시 사용
    if not force_reload and _is_cache_valid():
        return _load_from_cache()

    try:
        # Lazy import to avoid circular imports
        from app.services.google_sheets_service import google_sheets_service

        # Google Sheets 서비스 초기화 (range_name은 더 이상 사용하지 않음)
        await google_sheets_service.initialize(spreadsheet_id, "Sheet1!A:A")

        # 에러 코드 데이터 가져오기
        sheets_data = await google_sheets_service.get_error_codes()

        # 데이터 검증
        validation_errors = google_sheets_service.validate_error_codes(sheets_data)
        if validation_errors:
            print(f"경고: Google Sheets 데이터 검증 실패: {validation_errors}")
            # 검증 실패 시 캐시 파일이 있으면 사용
            if os.path.exists(CACHE_FILE):
                print("검증 실패로 인해 캐시 파일을 사용합니다.")
                return _load_from_cache()
            return False

        # 에러 코드 업데이트
        ERROR_CODES = sheets_data.copy()

        # 로컬 백업 파일 저장
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(ERROR_CODES, f, ensure_ascii=False, indent=2)

        print(
            f"Google Sheets에서 {len(sheets_data)}개의 에러 코드를 성공적으로 로드했습니다."
        )
        return True

    except Exception as e:
        print(f"Google Sheets에서 에러 코드 로드 실패: {str(e)}")

        # 실패 시 캐시 파일이 있으면 사용
        if os.path.exists(CACHE_FILE):
            print("Google Sheets 로드 실패로 인해 캐시 파일을 사용합니다.")
            return _load_from_cache()

        return False


def load_error_codes_from_file(file_path: str) -> bool:
    """
    로컬 JSON 파일에서 에러 코드를 로드합니다.

    Args:
        file_path: JSON 파일 경로

    Returns:
        성공 여부
    """
    global ERROR_CODES

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        # Lazy import to avoid circular imports
        from app.services.google_sheets_service import google_sheets_service

        # 데이터 검증
        validation_errors = google_sheets_service.validate_error_codes(file_data)
        if validation_errors:
            print(f"경고: 파일 데이터 검증 실패: {validation_errors}")
            return False

        ERROR_CODES = file_data.copy()
        print(
            f"로컬 파일에서 {len(file_data)}개의 에러 코드를 성공적으로 로드했습니다."
        )
        return True

    except Exception as e:
        print(f"로컬 파일에서 에러 코드 로드 실패: {str(e)}")
        return False


@lru_cache(maxsize=1)
def get_cached_error_codes() -> Dict[str, Dict[str, Any]]:
    """캐시된 에러 코드를 반환합니다."""
    return ERROR_CODES.copy()


def get_error_info(error_key: str, language: str = "ko") -> ErrorInfo:
    """
    에러 키로 에러 정보를 가져옵니다.

    Args:
        error_key: 에러 키 (예: "INVALID_CREDENTIALS")
        language: 언어 ("ko" 또는 "en") - 현재는 사용되지 않음 (객체에서 메서드로 처리)

    Returns:
        ErrorInfo 객체
    """
    if error_key not in ERROR_CODES:
        raise ValueError(f"Unknown error key: {error_key}")

    error_data = ERROR_CODES[error_key]
    return ErrorInfo(
        error_key=error_key,
        code=error_data["code"],
        message_ko=error_data["message_ko"],
        message_en=error_data["message_en"],
        dev_note=error_data.get("dev_note"),
    )


def raise_error(
    error_key: str, language: str = "ko", additional_data: Dict[str, Any] = None
) -> None:
    """
    에러를 발생시킵니다.

    Args:
        error_key: 에러 키 (예: "INVALID_CREDENTIALS")
        language: 언어 ("ko" 또는 "en")
        additional_data: 추가 데이터

    Raises:
        HTTPException: 해당 에러에 맞는 HTTP 예외
    """
    error_info = get_error_info(error_key, language)

    detail = {
        "error_code": error_key,
        "code": error_info.code,
        "message": error_info.get_message(language),
    }

    if additional_data:
        detail.update(additional_data)

    # HTTP 상태 코드는 에러 코드에서 가져와야 하는데, 현재 구조에서는 없으므로 기본값 사용
    # TODO: 에러 코드에 http_status 필드 추가 필요
    raise HTTPException(
        status_code=HttpStatus.BAD_REQUEST,  # 임시로 BAD_REQUEST 사용
        detail=detail,
    )


def get_error_response(
    error_key: str, language: str = "ko", additional_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    에러 응답을 생성합니다 (HTTPException을 발생시키지 않음).

    Args:
        error_key: 에러 키 (예: "INVALID_CREDENTIALS")
        language: 언어 ("ko" 또는 "en")
        additional_data: 추가 데이터

    Returns:
        에러 응답 딕셔너리
    """
    error_info = get_error_info(error_key, language)

    response = {
        "error_code": error_key,
        "code": error_info.code,
        "message": error_info.get_message(language),
        "dev_note": error_info.dev_note,
    }

    if additional_data:
        response.update(additional_data)

    return response
