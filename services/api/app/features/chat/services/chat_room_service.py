"""
채팅방 서비스
채팅방 목록 조회 및 정보 조회 담당
"""

import json
import logging
from datetime import datetime as dt
from typing import List

from redis.asyncio import Redis

from app.features.chat.repositories.chat_repository import ChatRepository
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.chat.schemas.chat_schemas import ChatMessageDto, ChatRoomDto
from app.features.chat.services.chat_message_service import ChatMessageService
from app.features.chat.services.chat_redis_cache_service import ChatRedisCacheService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChatRoomService:
    """채팅방 서비스 - 채팅방 목록 조회 및 정보 조회 담당"""

    def __init__(
        self,
        session: AsyncSession,
        redis: Redis | None = None,
    ):
        self._session = session
        self._redis = redis
        self._chat_room_repo = ChatRoomRepository(session)
        self._chat_repo = ChatRepository(session)
        self._message_service = ChatMessageService(session, redis)
        self._redis_cache = ChatRedisCacheService(redis) if redis else None

    # - MARK: 사용자의 채팅방 목록 조회
    async def get_user_chat_rooms(self, user_id: int) -> List[ChatRoomDto]:
        """사용자가 참여한 채팅방 목록 조회 (Redis 캐시 우선)"""
        # DB에서 사용자가 참여한 채팅방 목록 조회
        chat_rooms = await self._chat_room_repo.get_user_chat_rooms(user_id)

        rooms = []
        for chat_room in chat_rooms:
            # 활성 멤버 수 조회 (Redis 우선)
            member_count = await self._get_member_count_with_cache(chat_room.id)

            # 마지막 메시지 조회 (Redis 우선)
            last_message = await self._get_last_message_with_cache(chat_room.id)

            # Pod 정보 조회
            pod_id = chat_room.pod_id
            pod_title = None
            if chat_room.pod:
                pod_title = chat_room.pod.title

            # metadata 파싱
            metadata = None
            if chat_room.room_metadata:
                try:
                    metadata = json.loads(chat_room.room_metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = None

            rooms.append(
                ChatRoomDto(
                    id=chat_room.id,
                    name=chat_room.name,
                    cover_url=chat_room.cover_url,
                    metadata=metadata,
                    pod_id=pod_id,
                    pod_title=pod_title,
                    member_count=member_count,
                    last_message=last_message,
                    unread_count=await self._chat_room_repo.get_unread_count(
                        chat_room.id, user_id
                    ),
                    created_at=chat_room.created_at.isoformat()
                    if isinstance(chat_room.created_at, dt)
                    else "",
                    updated_at=chat_room.updated_at.isoformat()
                    if isinstance(chat_room.updated_at, dt)
                    else "",
                )
            )

        # 마지막 메시지 시간 기준으로 정렬
        rooms.sort(
            key=lambda r: r.last_message.created_at if r.last_message else dt.min,
            reverse=True,
        )

        return rooms

    # - MARK: 채팅방 상세 조회
    async def get_chat_room_detail(
        self, chat_room_id: int, user_id: int
    ) -> ChatRoomDto:
        """채팅방 상세 정보 조회 (Redis 캐시 우선)"""

        # 채팅방 조회
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ValueError(f"채팅방을 찾을 수 없습니다: {chat_room_id}")

        # 활성 멤버 수 조회 (Redis 우선)
        member_count = await self._get_member_count_with_cache(chat_room_id)

        # 마지막 메시지 조회 (Redis 우선)
        last_message = await self._get_last_message_with_cache(chat_room_id)

        # Pod 정보 조회
        pod_id = chat_room.pod_id

        # 읽지 않은 메시지 수 조회
        unread_count = await self._chat_room_repo.get_unread_count(
            chat_room_id, user_id
        )

        # metadata 파싱
        metadata = None
        if chat_room.room_metadata:
            try:
                metadata = json.loads(chat_room.room_metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = None

        return ChatRoomDto(
            id=chat_room.id,
            pod_id=pod_id,
            name=chat_room.name,
            cover_url=chat_room.cover_url,
            metadata=metadata,
            member_count=member_count,
            last_message=last_message,
            unread_count=unread_count,
            created_at=chat_room.created_at.isoformat()
            if isinstance(chat_room.created_at, dt)
            else "",
            updated_at=chat_room.updated_at.isoformat()
            if isinstance(chat_room.updated_at, dt)
            else "",
        )

    # - MARK: 채팅방 나가기
# - MARK: 채팅방 멤버 추가
    async def add_member(
        self, chat_room_id: int, user_id: int, role: str = "member"
    ) -> None:
        """채팅방에 멤버 추가 (DB + Redis 캐시)"""
        await self._chat_room_repo.add_member(chat_room_id, user_id, role)

        # Redis에도 멤버 추가
        if self._redis_cache:
            await self._redis_cache.add_member(chat_room_id, user_id)

    # - MARK: 읽음 처리
    async def mark_as_read(self, chat_room_id: int, user_id: int) -> None:
        """채팅방 읽음 처리 (검증은 use case에서 처리, commit은 use case에서 처리)"""
        await self._chat_room_repo.update_last_read_at(chat_room_id, user_id)

    # - MARK: 채팅방의 마지막 메시지 조회
    async def _get_last_message_by_room_id(self, chat_room_id: int):
        """채팅방 ID로 마지막 메시지 조회 (DB에서)"""
        return await self._chat_repo.get_last_message_by_room_id(chat_room_id)

    # - MARK: Redis 캐시를 활용한 마지막 메시지 조회
    async def _get_last_message_with_cache(
        self, chat_room_id: int
    ) -> ChatMessageDto | None:
        """마지막 메시지 조회 (Redis 우선, 없으면 DB 조회 후 캐시)"""
        # Redis에서 먼저 조회
        if self._redis_cache:
            cached_message = await self._redis_cache.get_last_message(chat_room_id)
            if cached_message:
                return cached_message

        # DB에서 조회
        last_message_model = await self._get_last_message_by_room_id(chat_room_id)
        if not last_message_model:
            return None

        # DTO 변환
        last_message = self._message_service._to_dto(
            last_message_model, last_message_model.user
        )

        # Redis에 캐시
        if self._redis_cache:
            await self._redis_cache.set_last_message(chat_room_id, last_message)

        return last_message

    # - MARK: Redis 캐시를 활용한 멤버 수 조회
    async def _get_member_count_with_cache(self, chat_room_id: int) -> int:
        """멤버 수 조회 (Redis 우선, 없으면 DB 조회 후 캐시)"""
        # Redis에서 먼저 조회
        if self._redis_cache:
            cached_count = await self._redis_cache.get_member_count(chat_room_id)
            if cached_count is not None:
                return cached_count

        # DB에서 조회
        active_members = await self._chat_room_repo.get_active_members(chat_room_id)
        member_count = len(active_members)

        # Redis에 멤버 목록 캐시
        if self._redis_cache and active_members:
            member_ids = [m.user_id for m in active_members]
            await self._redis_cache.set_members(chat_room_id, member_ids)

        return member_count

    # - MARK: Redis 캐시를 활용한 멤버 목록 조회
    async def get_members_with_cache(self, chat_room_id: int) -> List[int]:
        """멤버 ID 목록 조회 (Redis 우선, 없으면 DB 조회 후 캐시)"""
        # Redis에서 먼저 조회
        if self._redis_cache:
            cached_members = await self._redis_cache.get_members(chat_room_id)
            if cached_members is not None:
                return list(cached_members)

        # DB에서 조회
        active_members = await self._chat_room_repo.get_active_members(chat_room_id)
        member_ids = [m.user_id for m in active_members]

        # Redis에 캐시
        if self._redis_cache and member_ids:
            await self._redis_cache.set_members(chat_room_id, member_ids)

        return member_ids
