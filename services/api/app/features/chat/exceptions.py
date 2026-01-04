"""
Chat 도메인 전용 Exception 클래스

이 모듈은 Chat 도메인에서 발생할 수 있는 비즈니스 로직 예외를 정의합니다.
각 예외는 app/core/exceptions.py의 DomainException을 상속받아
app/core/error_codes.py (Google Sheets)에서 에러 정보를 자동으로 가져옵니다.
"""

from app.core.exceptions import DomainException


class ChatRoomNotFoundException(DomainException):
    """채팅방을 찾을 수 없는 경우"""

    def __init__(self, chat_room_id: int):
        super().__init__(
            error_key="CHAT_ROOM_NOT_FOUND", format_params={"chat_room_id": chat_room_id}
        )
        self.chat_room_id = chat_room_id


class ChatRoomAccessDeniedException(DomainException):
    """채팅방 접근 권한이 없는 경우"""

    def __init__(self, chat_room_id: int, user_id: int):
        super().__init__(
            error_key="CHAT_ROOM_ACCESS_DENIED",
            format_params={"chat_room_id": chat_room_id, "user_id": user_id},
        )
        self.chat_room_id = chat_room_id
        self.user_id = user_id


class ChatMemberNotFoundException(DomainException):
    """채팅방 멤버를 찾을 수 없는 경우"""

    def __init__(self, chat_room_id: int, user_id: int):
        super().__init__(
            error_key="CHAT_MEMBER_NOT_FOUND",
            format_params={"chat_room_id": chat_room_id, "user_id": user_id},
        )
        self.chat_room_id = chat_room_id
        self.user_id = user_id


class ChatMessageNotFoundException(DomainException):
    """채팅 메시지를 찾을 수 없는 경우"""

    def __init__(self, message_id: int):
        super().__init__(
            error_key="CHAT_MESSAGE_NOT_FOUND", format_params={"message_id": message_id}
        )
        self.message_id = message_id


class AlreadyChatMemberException(DomainException):
    """이미 채팅방 멤버인 경우"""

    def __init__(self, chat_room_id: int, user_id: int):
        super().__init__(
            error_key="ALREADY_CHAT_MEMBER",
            format_params={"chat_room_id": chat_room_id, "user_id": user_id},
        )
        self.chat_room_id = chat_room_id
        self.user_id = user_id
