"""ChatRoom Use Case - 채팅방 관련 비즈니스 로직 처리"""

import logging

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.chat.exceptions import (
    ChatRoomAccessDeniedException,
    ChatRoomNotFoundException,
)
from app.features.chat.repositories.chat_repository import ChatRepository
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.chat.schemas.chat_schemas import ChatMessageDto, ChatRoomDto
from app.features.chat.services.chat_redis_cache_service import ChatRedisCacheService
from app.features.chat.services.chat_room_dto_service import ChatRoomDtoService
from app.features.chat.services.message_dto_service import MessageDtoService

logger = logging.getLogger(__name__)


class ChatRoomUseCase:
    """채팅방 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        chat_room_repo: ChatRoomRepository,
        chat_repo: ChatRepository,
        redis: Redis | None = None,
    ) -> None:
        """
        Args:
            session: 데이터베이스 세션
            chat_room_repo: 채팅방 레포지토리
            chat_repo: 채팅 레포지토리
            redis: Redis 클라이언트 (선택적)
        """
        self._session = session
        self._chat_room_repo = chat_room_repo
        self._chat_repo = chat_repo
        self._redis_cache = ChatRedisCacheService(redis) if redis else None

    # MARK: - 사용자의 채팅방 목록 조회
    async def get_user_chat_rooms(self, user_id: int) -> list[ChatRoomDto]:
        """사용자가 참여한 채팅방 목록 조회 (Redis 캐시 우선)"""
        # DB에서 사용자가 참여한 채팅방 목록 조회
        chat_rooms = await self._chat_room_repo.get_user_chat_rooms(user_id)

        rooms: list[ChatRoomDto] = []
        for chat_room in chat_rooms:
            # 활성 멤버 수 조회 (Redis 우선)
            member_count = await self._get_member_count_with_cache(chat_room.id)

            # 마지막 메시지 조회 (Redis 우선)
            last_message = await self._get_last_message_with_cache(chat_room.id)

            # 읽지 않은 메시지 수 조회
            unread_count = await self._chat_room_repo.get_unread_count(
                chat_room.id, user_id
            )

            # DTO 변환
            room_dto = ChatRoomDtoService.convert_to_dto(
                chat_room=chat_room,
                member_count=member_count,
                last_message=last_message,
                unread_count=unread_count,
            )
            rooms.append(room_dto)

        # 마지막 메시지 시간 기준으로 정렬
        return ChatRoomDtoService.sort_by_last_message(rooms)

    # MARK: - 채팅방 상세 조회
    async def get_chat_room_detail(
        self, chat_room_id: int, user_id: int
    ) -> ChatRoomDto:
        """채팅방 상세 정보 조회 (비즈니스 로직 검증)"""
        # 채팅방 존재 확인
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ChatRoomNotFoundException(chat_room_id)

        # 사용자가 멤버인지 확인
        member = await self._chat_room_repo.get_member(chat_room_id, user_id)
        if not member or member.left_at:
            raise ChatRoomAccessDeniedException(chat_room_id, user_id)

        # 활성 멤버 수 조회 (Redis 우선)
        member_count = await self._get_member_count_with_cache(chat_room_id)

        # 마지막 메시지 조회 (Redis 우선)
        last_message = await self._get_last_message_with_cache(chat_room_id)

        # 읽지 않은 메시지 수 조회
        unread_count = await self._chat_room_repo.get_unread_count(
            chat_room_id, user_id
        )

        # DTO 변환
        return ChatRoomDtoService.convert_to_dto(
            chat_room=chat_room,
            member_count=member_count,
            last_message=last_message,
            unread_count=unread_count,
        )

    # MARK: - 읽음 처리
    async def mark_as_read(self, chat_room_id: int, user_id: int) -> None:
        """채팅방 읽음 처리 (비즈니스 로직 검증)"""
        # 채팅방 존재 확인
        chat_room = await self._chat_room_repo.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            raise ChatRoomNotFoundException(chat_room_id)

        # 사용자가 멤버인지 확인
        member = await self._chat_room_repo.get_member(chat_room_id, user_id)
        if not member or member.left_at:
            raise ChatRoomAccessDeniedException(chat_room_id, user_id)

        # 읽음 처리
        try:
            await self._chat_room_repo.update_last_read_at(chat_room_id, user_id)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 채팅방 멤버 추가
    async def add_member(
        self, chat_room_id: int, user_id: int, role: str = "member"
    ) -> None:
        """채팅방에 멤버 추가 (DB + Redis 캐시)"""
        await self._chat_room_repo.add_member(chat_room_id, user_id, role)

        # Redis에도 멤버 추가
        if self._redis_cache:
            await self._redis_cache.add_member(chat_room_id, user_id)

    # MARK: - Redis 캐시를 활용한 멤버 목록 조회
    async def get_members_with_cache(self, chat_room_id: int) -> list[int]:
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

    # MARK: - Private: 채팅방의 마지막 메시지 조회
    async def _get_last_message_by_room_id(self, chat_room_id: int):
        """채팅방 ID로 마지막 메시지 조회 (DB에서)"""
        return await self._chat_repo.get_last_message_by_room_id(chat_room_id)

    # MARK: - Private: Redis 캐시를 활용한 마지막 메시지 조회
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
        last_message = MessageDtoService.convert_to_dto(
            last_message_model, last_message_model.user
        )

        # Redis에 캐시
        if self._redis_cache:
            await self._redis_cache.set_last_message(chat_room_id, last_message)

        return last_message

    # MARK: - Private: Redis 캐시를 활용한 멤버 수 조회
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
