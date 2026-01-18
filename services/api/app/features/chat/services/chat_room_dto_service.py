"""
채팅방 DTO 변환 서비스
ChatRoom 모델을 ChatRoomDto로 변환하는 로직 담당
"""

import json
from datetime import datetime as dt

from app.features.chat.models import ChatRoom
from app.features.chat.schemas.chat_schemas import ChatMessageDto, ChatRoomDto
from app.features.pods.models import Pod


class ChatRoomDtoService:
    """채팅방 DTO 변환 서비스 (Stateless)"""

    @staticmethod
    def convert_to_dto(
        chat_room: ChatRoom,
        member_count: int,
        last_message: ChatMessageDto | None,
        unread_count: int,
    ) -> ChatRoomDto:
        """ChatRoom 모델을 ChatRoomDto로 변환

        Args:
            chat_room: 채팅방 모델
            member_count: 활성 멤버 수
            last_message: 마지막 메시지 DTO
            unread_count: 읽지 않은 메시지 수

        Returns:
            ChatRoomDto: 변환된 DTO
        """
        # Pod 정보 조회
        pod: Pod | None = chat_room.pod
        pod_id: int | None = chat_room.pod_id
        pod_title: str | None = pod.title if pod else None

        # metadata 파싱
        metadata: dict | None = ChatRoomDtoService._parse_metadata(
            chat_room.room_metadata
        )

        # 시간 포맷팅
        created_at_str: str = ChatRoomDtoService._format_datetime(chat_room.created_at)
        updated_at_str: str = ChatRoomDtoService._format_datetime(chat_room.updated_at)

        return ChatRoomDto(
            id=chat_room.id,
            name=chat_room.name,
            cover_url=chat_room.cover_url,
            metadata=metadata,
            pod_id=pod_id,
            pod_title=pod_title,
            member_count=member_count,
            last_message=last_message,
            unread_count=unread_count,
            created_at=created_at_str,
            updated_at=updated_at_str,
        )

    @staticmethod
    def _parse_metadata(room_metadata: str | None) -> dict | None:
        """room_metadata JSON 문자열을 dict로 파싱"""
        if not room_metadata:
            return None
        try:
            return json.loads(room_metadata)
        except (json.JSONDecodeError, TypeError):
            return None

    @staticmethod
    def _format_datetime(datetime_value: dt | None) -> str:
        """datetime을 ISO 포맷 문자열로 변환"""
        if isinstance(datetime_value, dt):
            return datetime_value.isoformat()
        return ""

    @staticmethod
    def sort_by_last_message(rooms: list[ChatRoomDto]) -> list[ChatRoomDto]:
        """마지막 메시지 시간 기준으로 정렬 (최신순)

        Args:
            rooms: 정렬할 채팅방 DTO 리스트

        Returns:
            list[ChatRoomDto]: 정렬된 리스트
        """
        return sorted(
            rooms,
            key=lambda r: r.last_message.created_at if r.last_message else dt.min,
            reverse=True,
        )
