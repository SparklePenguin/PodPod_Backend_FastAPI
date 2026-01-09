"""
채팅 Redis 캐시 서비스
채팅방 관련 데이터를 Redis에 캐시하여 성능 최적화
"""

import json
import logging
from datetime import datetime
from typing import List, Set

from redis.asyncio import Redis

from app.features.chat.schemas.chat_schemas import ChatMessageDto, MessageType

logger = logging.getLogger(__name__)

# Redis 키 prefix
CHAT_ROOM_PREFIX = "chat:room"
CHAT_USER_PREFIX = "chat:user"

# TTL 설정 (초)
LAST_MESSAGE_TTL = 60 * 60 * 24  # 24시간
MEMBER_TTL = 60 * 60 * 24  # 24시간
CONNECTED_USER_TTL = 60 * 60  # 1시간 (접속 상태는 더 짧게)


class ChatRedisCacheService:
    """채팅 Redis 캐시 서비스"""

    def __init__(self, redis: Redis):
        self._redis = redis

    # ========== 키 생성 헬퍼 ==========

    def _last_message_key(self, room_id: int) -> str:
        return f"{CHAT_ROOM_PREFIX}:{room_id}:last_message"

    def _members_key(self, room_id: int) -> str:
        return f"{CHAT_ROOM_PREFIX}:{room_id}:members"

    def _connected_users_key(self, room_id: int) -> str:
        return f"{CHAT_ROOM_PREFIX}:{room_id}:connected"

    def _user_rooms_key(self, user_id: int) -> str:
        return f"{CHAT_USER_PREFIX}:{user_id}:rooms"

    # ========== 마지막 메시지 캐시 ==========

    async def set_last_message(self, room_id: int, message: ChatMessageDto) -> None:
        """채팅방의 마지막 메시지를 Redis에 저장"""
        try:
            key = self._last_message_key(room_id)
            # ChatMessageDto를 JSON으로 직렬화
            message_dict = {
                "id": message.id,
                "user_id": message.user_id,
                "nickname": message.nickname,
                "profile_image": message.profile_image,
                "message": message.message,
                "message_type": message.message_type.value,
                "created_at": message.created_at.isoformat(),
            }
            await self._redis.set(
                key, json.dumps(message_dict, ensure_ascii=False), ex=LAST_MESSAGE_TTL
            )
            logger.debug(f"Redis 마지막 메시지 캐시 저장: room_id={room_id}")
        except Exception as e:
            logger.error(f"Redis 마지막 메시지 캐시 저장 실패: {e}")

    async def get_last_message(self, room_id: int) -> ChatMessageDto | None:
        """채팅방의 마지막 메시지를 Redis에서 조회"""
        try:
            key = self._last_message_key(room_id)
            data = await self._redis.get(key)
            if not data:
                return None

            message_dict = json.loads(data)
            return ChatMessageDto(
                id=message_dict["id"],
                user_id=message_dict["user_id"],
                nickname=message_dict.get("nickname"),
                profile_image=message_dict.get("profile_image"),
                message=message_dict["message"],
                message_type=MessageType(message_dict["message_type"]),
                created_at=datetime.fromisoformat(message_dict["created_at"]),
            )
        except Exception as e:
            logger.error(f"Redis 마지막 메시지 캐시 조회 실패: {e}")
            return None

    async def delete_last_message(self, room_id: int) -> None:
        """채팅방의 마지막 메시지 캐시 삭제"""
        try:
            key = self._last_message_key(room_id)
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis 마지막 메시지 캐시 삭제 실패: {e}")

    # ========== 채팅방 멤버 캐시 ==========

    async def add_member(self, room_id: int, user_id: int) -> None:
        """채팅방에 멤버 추가 (Redis Set)"""
        try:
            key = self._members_key(room_id)
            await self._redis.sadd(key, str(user_id))
            await self._redis.expire(key, MEMBER_TTL)

            # 사용자의 채팅방 목록에도 추가
            user_key = self._user_rooms_key(user_id)
            await self._redis.sadd(user_key, str(room_id))
            await self._redis.expire(user_key, MEMBER_TTL)

            logger.debug(f"Redis 멤버 추가: room_id={room_id}, user_id={user_id}")
        except Exception as e:
            logger.error(f"Redis 멤버 추가 실패: {e}")

    async def remove_member(self, room_id: int, user_id: int) -> None:
        """채팅방에서 멤버 제거 (Redis Set)"""
        try:
            key = self._members_key(room_id)
            await self._redis.srem(key, str(user_id))

            # 사용자의 채팅방 목록에서도 제거
            user_key = self._user_rooms_key(user_id)
            await self._redis.srem(user_key, str(room_id))

            logger.debug(f"Redis 멤버 제거: room_id={room_id}, user_id={user_id}")
        except Exception as e:
            logger.error(f"Redis 멤버 제거 실패: {e}")

    async def get_members(self, room_id: int) -> Set[int] | None:
        """채팅방 멤버 목록 조회 (Redis에 없으면 None 반환)"""
        try:
            key = self._members_key(room_id)
            members = await self._redis.smembers(key)
            if not members:
                return None
            return {int(m) for m in members}
        except Exception as e:
            logger.error(f"Redis 멤버 조회 실패: {e}")
            return None

    async def set_members(self, room_id: int, user_ids: List[int]) -> None:
        """채팅방 멤버 목록 전체 설정 (DB에서 로드 후 캐시할 때 사용)"""
        try:
            key = self._members_key(room_id)
            if user_ids:
                await self._redis.delete(key)
                await self._redis.sadd(key, *[str(uid) for uid in user_ids])
                await self._redis.expire(key, MEMBER_TTL)
            logger.debug(f"Redis 멤버 목록 설정: room_id={room_id}, count={len(user_ids)}")
        except Exception as e:
            logger.error(f"Redis 멤버 목록 설정 실패: {e}")

    async def get_member_count(self, room_id: int) -> int | None:
        """채팅방 멤버 수 조회"""
        try:
            key = self._members_key(room_id)
            count = await self._redis.scard(key)
            return count if count > 0 else None
        except Exception as e:
            logger.error(f"Redis 멤버 수 조회 실패: {e}")
            return None

    async def is_member(self, room_id: int, user_id: int) -> bool | None:
        """사용자가 채팅방 멤버인지 확인 (캐시 miss면 None 반환)"""
        try:
            key = self._members_key(room_id)
            # 키가 존재하는지 먼저 확인
            if not await self._redis.exists(key):
                return None
            return await self._redis.sismember(key, str(user_id))
        except Exception as e:
            logger.error(f"Redis 멤버 확인 실패: {e}")
            return None

    # ========== 접속 중인 사용자 캐시 ==========

    async def set_user_connected(self, room_id: int, user_id: int) -> None:
        """사용자 접속 상태 설정"""
        try:
            key = self._connected_users_key(room_id)
            await self._redis.sadd(key, str(user_id))
            await self._redis.expire(key, CONNECTED_USER_TTL)
            logger.debug(f"Redis 사용자 접속: room_id={room_id}, user_id={user_id}")
        except Exception as e:
            logger.error(f"Redis 사용자 접속 설정 실패: {e}")

    async def set_user_disconnected(self, room_id: int, user_id: int) -> None:
        """사용자 접속 해제 상태 설정"""
        try:
            key = self._connected_users_key(room_id)
            await self._redis.srem(key, str(user_id))
            logger.debug(f"Redis 사용자 접속 해제: room_id={room_id}, user_id={user_id}")
        except Exception as e:
            logger.error(f"Redis 사용자 접속 해제 설정 실패: {e}")

    async def is_user_connected(self, room_id: int, user_id: int) -> bool:
        """사용자가 채팅방에 접속 중인지 확인"""
        try:
            key = self._connected_users_key(room_id)
            return await self._redis.sismember(key, str(user_id))
        except Exception as e:
            logger.error(f"Redis 사용자 접속 확인 실패: {e}")
            return False

    async def get_connected_users(self, room_id: int) -> Set[int]:
        """채팅방에 접속 중인 사용자 목록 조회"""
        try:
            key = self._connected_users_key(room_id)
            users = await self._redis.smembers(key)
            return {int(u) for u in users} if users else set()
        except Exception as e:
            logger.error(f"Redis 접속 사용자 조회 실패: {e}")
            return set()

    # ========== 사용자별 채팅방 목록 ==========

    async def get_user_rooms(self, user_id: int) -> Set[int] | None:
        """사용자가 참여한 채팅방 목록 조회"""
        try:
            key = self._user_rooms_key(user_id)
            rooms = await self._redis.smembers(key)
            if not rooms:
                return None
            return {int(r) for r in rooms}
        except Exception as e:
            logger.error(f"Redis 사용자 채팅방 조회 실패: {e}")
            return None

    async def set_user_rooms(self, user_id: int, room_ids: List[int]) -> None:
        """사용자의 채팅방 목록 전체 설정"""
        try:
            key = self._user_rooms_key(user_id)
            if room_ids:
                await self._redis.delete(key)
                await self._redis.sadd(key, *[str(rid) for rid in room_ids])
                await self._redis.expire(key, MEMBER_TTL)
            logger.debug(f"Redis 사용자 채팅방 설정: user_id={user_id}, count={len(room_ids)}")
        except Exception as e:
            logger.error(f"Redis 사용자 채팅방 설정 실패: {e}")

    # ========== 캐시 무효화 ==========

    async def invalidate_room_cache(self, room_id: int) -> None:
        """채팅방 관련 모든 캐시 무효화"""
        try:
            keys = [
                self._last_message_key(room_id),
                self._members_key(room_id),
                self._connected_users_key(room_id),
            ]
            await self._redis.delete(*keys)
            logger.debug(f"Redis 채팅방 캐시 무효화: room_id={room_id}")
        except Exception as e:
            logger.error(f"Redis 채팅방 캐시 무효화 실패: {e}")
