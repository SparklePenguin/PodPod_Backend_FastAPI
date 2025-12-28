"""
채팅 라우터
"""

import logging

from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.service import get_chat_service
from app.features.chat.schemas.chat_message_dto import ChatMessageDto
from app.features.chat.schemas.chat_room_dto import ChatRoomDto
from app.features.chat.schemas.chat_room_list_dto import ChatRoomListDto
from app.features.chat.schemas.send_message_request import SendMessageRequest
from app.features.chat.services.chat_service import ChatService
from fastapi import APIRouter, Depends, Path, Query, status

router = APIRouter()
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


# - MARK: 채널의 메시지 목록 조회
@router.get(
    "/rooms/{channel_url}/messages",
    response_model=BaseResponse[PageDto[ChatMessageDto]],
    description="채팅 메시지 목록 조회",
)
async def get_messages(
    channel_url: str = Path(..., description="채널 URL"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(50, ge=1, le=100, description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """채널의 메시지 목록 조회"""
    messages, total_count = await service.get_messages(channel_url, page, size)
    return BaseResponse.ok(
        data=PageDto(items=messages, total_count=total_count, page=page, size=size),
        http_status=status.HTTP_200_OK,
    )


# - MARK: 메시지 전송
@router.post(
    "/rooms/{channel_url}/messages",
    response_model=BaseResponse[ChatMessageDto],
    description="메시지 전송",
)
async def send_message(
    channel_url: str = Path(..., description="채널 URL"),
    request: SendMessageRequest = ...,
    current_user_id: int = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
):
    """메시지 전송"""
    message = await service.send_message(
        channel_url=channel_url,
        user_id=current_user_id,
        message=request.message,
        message_type=request.message_type,
    )
    return BaseResponse.ok(data=message, http_status=status.HTTP_201_CREATED)
