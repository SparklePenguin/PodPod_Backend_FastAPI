"""
Tendencies 도메인 전용 Exception 클래스

이 모듈은 Tendencies 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.
"""

from app.core.exceptions import DomainException


class TendencyResultNotFoundException(DomainException):
    """성향 테스트 결과를 찾을 수 없는 경우"""

    def __init__(self, tendency_type: str | None = None):
        super().__init__(
            error_key="TENDENCY_RESULT_NOT_FOUND",
            format_params={"tendency_type": tendency_type or "unknown"},
        )
        self.tendency_type = tendency_type


class TendencySurveyNotFoundException(DomainException):
    """성향 테스트 설문을 찾을 수 없는 경우"""

    def __init__(self):
        super().__init__(error_key="TENDENCY_SURVEY_NOT_FOUND")
