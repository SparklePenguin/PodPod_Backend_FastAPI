"""
Notifications 도메인 전용 Exception 클래스

이 모듈은 Notifications 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.
"""

from app.core.exceptions import DomainException


class NotificationNotFoundException(DomainException):
    """알림을 찾을 수 없거나 권한이 없는 경우"""

    def __init__(self, notification_id: int):
        super().__init__(
            error_key="NOTIFICATION_NOT_FOUND",
            format_params={"notification_id": notification_id},
        )
        self.notification_id = notification_id
