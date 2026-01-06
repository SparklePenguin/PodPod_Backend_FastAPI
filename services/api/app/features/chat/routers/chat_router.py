"""
채팅 라우터
"""

import logging

from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.providers import get_chat_service, get_chat_use_case
from app.features.chat.schemas.chat_schemas import (
    ChatMessageDto,
    ChatRoomDto,
    ChatRoomListDto,
    SendMessageRequest,
)
from app.features.chat.services.chat_service import ChatService
from app.features.chat.use_cases.chat_use_case import ChatUseCase
from fastapi import APIRouter, Depends, Path, Query, status

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


# - MARK: 채팅방 목록 조회
@router.get(
    "/rooms",
    response_model=BaseResponse[ChatRoomListDto],
    description="채팅방 목록 조회",
)
async def get_chat_rooms(
    current_user_id: int = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """사용자가 참여한 채팅방 목록 조회"""
    rooms = await service.get_user_chat_rooms(current_user_id)
    return BaseResponse.ok(
        data=ChatRoomListDto(rooms=rooms, total_count=len(rooms)),
        http_status=status.HTTP_200_OK,
    )


# - MARK: 채팅방 상세 조회
@router.get(
    "/rooms/{room_id}",
    response_model=BaseResponse[ChatRoomDto],
    description="채팅방 상세 조회",
)
async def get_chat_room(
    room_id: int = Path(..., description="채팅방 ID", alias="roomId"),
    current_user_id: int = Depends(get_current_user_id),
    use_case: ChatUseCase = Depends(get_chat_use_case),
):
    """채팅방 상세 정보 조회"""
    room = await use_case.get_chat_room_detail(room_id, current_user_id)
    return BaseResponse.ok(data=room, http_status=status.HTTP_200_OK)


# - MARK: 채팅방 메시지 목록 조회
@router.get(
    "/rooms/{room_id}/messages",
    response_model=BaseResponse[PageDto[ChatMessageDto]],
    description="채팅 메시지 목록 조회",
)
async def get_messages(
    room_id: int = Path(..., description="채팅방 ID", alias="roomId"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(50, ge=1, le=100, description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    use_case: ChatUseCase = Depends(get_chat_use_case),
):
    """채팅방의 메시지 목록 조회"""
    messages, total_count = await use_case.get_messages_by_room_id(room_id, current_user_id, page, size)
    return BaseResponse.ok(
        data=PageDto(items=messages, total_count=total_count, page=page, size=size),
        http_status=status.HTTP_200_OK,
    )


# - MARK: 메시지 전송
@router.post(
    "/rooms/{room_id}/messages",
    response_model=BaseResponse[ChatMessageDto],
    description="메시지 전송",
)
async def send_message(
    room_id: int = Path(..., description="채팅방 ID", alias="roomId"),
    request: SendMessageRequest = ...,
    current_user_id: int = Depends(get_current_user_id),
    use_case: ChatUseCase = Depends(get_chat_use_case),
):
    """메시지 전송"""
    message = await use_case.send_message_by_room_id(
        chat_room_id=room_id,
        user_id=current_user_id,
        message=request.message,
        message_type=request.message_type,
    )
    return BaseResponse.ok(data=message, http_status=status.HTTP_201_CREATED)


# - MARK: 채팅방 나가기
@router.delete(
    "/rooms/{room_id}/members",
    response_model=BaseResponse[dict],
    description="채팅방 나가기",
)
async def leave_chat_room(
    room_id: int = Path(..., description="채팅방 ID", alias="roomId"),
    current_user_id: int = Depends(get_current_user_id),
    use_case: ChatUseCase = Depends(get_chat_use_case),
):
    """채팅방 나가기"""
    await use_case.leave_chat_room(room_id, current_user_id)
    return BaseResponse.ok(
        data={"success": True}, http_status=status.HTTP_200_OK
    )


# - MARK: 읽음 처리
@router.put(
    "/rooms/{room_id}/read",
    response_model=BaseResponse[dict],
    description="채팅방 읽음 처리",
)
async def mark_chat_room_as_read(
    room_id: int = Path(..., description="채팅방 ID", alias="roomId"),
    current_user_id: int = Depends(get_current_user_id),
    use_case: ChatUseCase = Depends(get_chat_use_case),
):
    """채팅방 읽음 처리"""
    await use_case.mark_as_read(room_id, current_user_id)
    return BaseResponse.ok(
        data={"success": True}, http_status=status.HTTP_200_OK
    )
