"""
Chat 도메인 전용 Exception Handler

이 모듈은 Chat 도메인의 예외를 처리하는 핸들러를 정의합니다.
각 핸들러는 BaseResponse 패턴으로 일관된 응답을 반환합니다.

중요: 이 파일은 반드시 EXCEPTION_HANDLERS 딕셔너리를 export해야 합니다.
     이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
"""

from app.common.schemas import BaseResponse
from app.features.chat.exceptions import (
    AlreadyChatMemberException,
    ChatMemberNotFoundException,
    ChatMessageNotFoundException,
    ChatRoomAccessDeniedException,
    ChatRoomNotFoundException,
)
from fastapi import Request
from fastapi.responses import JSONResponse


async def chat_room_not_found_handler(request: Request, exc: ChatRoomNotFoundException):
    """ChatRoomNotFoundException 처리: 채팅방을 찾을 수 없는 경우"""

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


async def chat_room_access_denied_handler(
    request: Request, exc: ChatRoomAccessDeniedException
):
    """ChatRoomAccessDeniedException 처리: 채팅방 접근 권한이 없는 경우"""

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


async def chat_member_not_found_handler(
    request: Request, exc: ChatMemberNotFoundException
):
    """ChatMemberNotFoundException 처리: 채팅방 멤버를 찾을 수 없는 경우"""

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


async def chat_message_not_found_handler(
    request: Request, exc: ChatMessageNotFoundException
):
    """ChatMessageNotFoundException 처리: 채팅 메시지를 찾을 수 없는 경우"""

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


async def already_chat_member_handler(
    request: Request, exc: AlreadyChatMemberException
):
    """AlreadyChatMemberException 처리: 이미 채팅방 멤버인 경우"""

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


# 자동 등록을 위한 핸들러 매핑
# 이 딕셔너리는 app/core/exception_loader.py에서 자동으로 읽어서 등록됩니다.
EXCEPTION_HANDLERS = {
    ChatRoomNotFoundException: chat_room_not_found_handler,
    ChatRoomAccessDeniedException: chat_room_access_denied_handler,
    ChatMemberNotFoundException: chat_member_not_found_handler,
    ChatMessageNotFoundException: chat_message_not_found_handler,
    AlreadyChatMemberException: already_chat_member_handler,
}
