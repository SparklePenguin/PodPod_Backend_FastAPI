"""
Artists 도메인 전용 Exception 클래스

이 모듈은 Artists 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.

사용법:
    1. Google Sheets에 에러 키 등록 (예: ARTIST_NOT_FOUND)
    2. 이 파일에서 Exception 클래스 정의 (error_key만 지정)
    3. 서비스에서 예외 발생 시 자동으로 메시지 로드
"""

from app.core.exceptions import DomainException


class ArtistNotFoundException(DomainException):
    """아티스트를 찾을 수 없는 경우"""

    def __init__(self, artist_id: int):
        super().__init__(
            error_key="ARTIST_NOT_FOUND",
            format_params={"artist_id": artist_id},
        )
        self.artist_id = artist_id


class ArtistScheduleNotFoundException(DomainException):
    """아티스트 스케줄을 찾을 수 없는 경우"""

    def __init__(self, schedule_id: int):
        super().__init__(
            error_key="ARTIST_SCHEDULE_NOT_FOUND",
            format_params={"schedule_id": schedule_id},
        )
        self.schedule_id = schedule_id


class ArtistSuggestionNotFoundException(DomainException):
    """아티스트 추천을 찾을 수 없는 경우"""

    def __init__(self, suggestion_id: int):
        super().__init__(
            error_key="ARTIST_SUGGESTION_NOT_FOUND",
            format_params={"suggestion_id": suggestion_id},
        )
        self.suggestion_id = suggestion_id


class ArtistAlreadyExistsException(DomainException):
    """이미 존재하는 아티스트인 경우"""

    def __init__(self, artist_name: str):
        super().__init__(
            error_key="ARTIST_ALREADY_EXISTS",
            format_params={"artist_name": artist_name},
        )
        self.artist_name = artist_name
