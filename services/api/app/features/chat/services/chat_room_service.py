"""
채팅방 서비스
채팅방 목록 조회 및 정보 조회 담당
"""

import logging
from datetime import datetime as dt
from typing import List

from app.features.chat.repositories.chat_repository import ChatRepository
from app.features.chat.schemas.chat_room_dto import ChatRoomDto
from app.features.chat.services.chat_message_service import ChatMessageService
from app.features.chat.services.chat_pod_service import ChatPodService
from app.features.chat.services.chat_websocket_service import ChatWebSocketService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChatRoomService:
    """채팅방 서비스 - 채팅방 목록 조회 및 정보 조회 담당"""

    def __init__(
        self,
        session: AsyncSession,
        websocket_service: ChatWebSocketService | None = None,
    ):
        self._session = session
        self._chat_repo = ChatRepository(session)
        self._message_service = ChatMessageService(session)
        self._pod_service = ChatPodService(session)
        self._websocket_service = websocket_service

    # - MARK: 사용자의 채팅방 목록 조회
    async def get_user_chat_rooms(self, user_id: int) -> List[ChatRoomDto]:
        """사용자가 참여한 채팅방 목록 조회"""
        # 사용자가 메시지를 보낸 채널 목록 조회
        channel_urls = await self._chat_repo.get_user_channels(user_id)

        rooms = []
        for channel_url in channel_urls:
            # 채널 메타데이터 조회
            channel_metadata = None
            if self._websocket_service:
                channel_metadata = await self._websocket_service.get_channel_metadata(
                    channel_url
                )

            if not channel_metadata:
                continue

            # 마지막 메시지 조회
            last_message = await self._message_service.get_last_message(channel_url)

            # Pod 정보 추출
            pod_id, pod_title = self._pod_service.extract_pod_info_from_metadata(
                channel_metadata, channel_url
            )

            # 멤버 수
            members = channel_metadata.get("members", [])
            member_count = len(members)

            rooms.append(
                ChatRoomDto(
                    channel_url=channel_url,
                    name=channel_metadata.get("name", channel_url),
                    cover_url=channel_metadata.get("cover_url"),
                    pod_id=pod_id,
                    pod_title=pod_title,
                    member_count=member_count,
                    last_message=last_message,
                    unread_count=0,  # TODO: 읽지 않은 메시지 수 계산
                    created_at=channel_metadata.get("created_at", ""),
                )
            )

        # 마지막 메시지 시간 기준으로 정렬
        rooms.sort(
            key=lambda r: r.last_message.created_at
            if r.last_message
            else dt.min.replace(tzinfo=None),
            reverse=True,
        )

        return rooms
