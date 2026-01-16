"""
비즈니스 예외 베이스 클래스들
"""

import logging

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """비즈니스 로직 예외"""

    def __init__(
        self,
        error_code: str,
        message_ko: str,
        message_en: str | None = None,
        status_code: int = 400,
        dev_note: str | None = None,
    ):
        self.error_code = error_code
        self.message_ko = message_ko
        self.message_en = message_en or message_ko
        self.status_code = status_code
        self.dev_note = dev_note or "Business logic error"
        super().__init__(self.message_ko)


class DomainException(BusinessException):
    """
    도메인별 예외 베이스 클래스 (error_codes.py와 연계)

    이 클래스를 상속받으면 error_key만으로 Google Sheets의 에러 정보를 자동으로 가져옵니다.
    메시지 포맷팅을 위한 추가 파라미터를 지원합니다.

    Example:
        class PodNotFoundException(DomainException):
            def __init__(self, pod_id: int):
                super().__init__(
                    error_key="POD_NOT_FOUND",
                    format_params={"pod_id": pod_id}
                )
                self.pod_id = pod_id
    """

    def __init__(
        self,
        error_key: str,
        format_params: dict | None = None,
        override_message_ko: str | None = None,
        override_message_en: str | None = None,
        override_status_code: int | None = None,
        override_dev_note: str | None = None,
    ):
        """
        DomainException 초기화

        Args:
            error_key: ERROR_CODES에 정의된 에러 키 (예: "POD_NOT_FOUND")
            format_params: 메시지 포맷팅용 파라미터 (예: {"pod_id": 123})
            override_message_ko: 메시지 한국어 오버라이드 (선택)
            override_message_en: 메시지 영어 오버라이드 (선택)
            override_status_code: HTTP 상태 코드 오버라이드 (선택)
            override_dev_note: 개발자 노트 오버라이드 (선택)
        """
        from .registry import get_error_info

        self.error_key = error_key
        self.format_params = format_params or {}

        # ERROR_CODES에서 에러 정보 가져오기
        try:
            error_info = get_error_info(error_key)

            # 메시지 포맷팅 (format_params가 있으면 적용)
            message_ko = override_message_ko or error_info.message_ko
            message_en = override_message_en or error_info.message_en

            if self.format_params:
                try:
                    message_ko = message_ko.format(**self.format_params)
                    message_en = message_en.format(**self.format_params)
                except KeyError:
                    # 포맷팅 실패 시 원본 메시지 사용
                    pass

            status_code = override_status_code or error_info.http_status
            dev_note = override_dev_note or error_info.dev_note
            error_code_num = error_info.code

        except (ValueError, KeyError):
            # ERROR_CODES에 없는 경우 기본값 사용
            logger.warning(
                f"Error key '{error_key}' not found in ERROR_CODES, using defaults"
            )
            message_ko = override_message_ko or f"에러가 발생했습니다. ({error_key})"
            message_en = override_message_en or f"An error occurred ({error_key})"
            status_code = override_status_code or 400
            dev_note = override_dev_note or f"Error: {error_key}"
            error_code_num = 9999

        # 부모 클래스 초기화
        super().__init__(
            error_code=error_key,
            message_ko=message_ko,
            message_en=message_en,
            status_code=status_code,
            dev_note=dev_note,
        )

        # 추가 속성 저장
        self.error_code_num = error_code_num
