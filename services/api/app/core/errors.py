"""
PodPod Backend API 에러 코드 체계

에러 코드는 errors.json에서 도메인별로 관리됩니다.
동기화는 scripts/sync_error_codes_to_sheet.py로 수행합니다.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException


@dataclass
class ErrorInfo:
    """에러 정보를 담는 객체"""

    error_key: str
    code: int
    message_ko: str
    message_en: str
    http_status: int
    dev_note: str | None = None

    @property
    def message(self) -> str:
        """기본 메시지 (한국어)"""
        return self.message_ko

    def get_message(self, language: str = "ko") -> str:
        """언어에 따른 메시지 반환"""
        if language == "en":
            return self.message_en
        return self.message_ko


# errors.json 경로
ERRORS_JSON_PATH = Path(__file__).parent / "errors.json"

# 에러 코드 (errors.json에서 로드됨)
ERROR_CODES: Dict[str, Dict[str, Any]] = {}


def _load_errors_from_json() -> None:
    """errors.json에서 에러 코드를 로드합니다."""
    global ERROR_CODES

    if not ERRORS_JSON_PATH.exists():
        print(f"경고: errors.json 파일을 찾을 수 없습니다: {ERRORS_JSON_PATH}")
        return

    try:
        with open(ERRORS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 도메인별 구조를 flat하게 변환
        for domain, errors in data.items():
            for error_key, error_data in errors.items():
                ERROR_CODES[error_key] = error_data

        print(f"errors.json에서 {len(ERROR_CODES)}개의 에러 코드를 로드했습니다.")

    except Exception as e:
        print(f"errors.json 로드 실패: {str(e)}")


# 모듈 로드 시 자동으로 에러 코드 로드
_load_errors_from_json()


def get_error_codes() -> Dict[str, Dict[str, Any]]:
    """에러 코드 딕셔너리를 반환합니다."""
    return ERROR_CODES.copy()


def get_error_info(error_key: str, language: str = "ko") -> ErrorInfo:
    """
    에러 키로 에러 정보를 가져옵니다.

    Args:
        error_key: 에러 키 (예: "INVALID_CREDENTIALS")
        language: 언어 ("ko" 또는 "en")

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
        http_status=error_data["http_status"],
        dev_note=error_data.get("dev_note"),
    )


def raise_error(
    error_key: str, language: str = "ko", additional_data: Dict[str, Any] | None = None
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

    raise HTTPException(
        status_code=error_info.http_status,
        detail=detail,
    )


def get_error_response(
    error_key: str, language: str = "ko", additional_data: Dict[str, Any] | None = None
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
