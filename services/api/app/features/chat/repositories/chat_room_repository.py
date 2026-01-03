"""
채팅방 Repository
"""

import json
from typing import Dict, List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.chat.models.chat_room import ChatMember, ChatRoom


class ChatRoomRepository:
    """채팅방 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 채팅방 생성
    async def create_chat_room(
        self,
        pod_id: int,
        name: str,
        cover_url: str | None = None,
        metadata: Dict | None = None,
        owner_id: int | None = None,
    ) -> ChatRoom:
        """채팅방 생성"""
        chat_room = ChatRoom(
            pod_id=pod_id,
            name=name,
            cover_url=cover_url,
            room_metadata=json.dumps(metadata) if metadata else None,
            is_active=True,
        )
        self._session.add(chat_room)
        await self._session.flush()
        await self._session.refresh(chat_room)

        # 파티장을 채팅방 멤버로 추가
        if owner_id:
            await self.add_member(chat_room.id, owner_id, role="owner")

        return chat_room

    # - MARK: 채팅방 조회
    async def get_chat_room_by_pod_id(self, pod_id: int) -> ChatRoom | None:
        """파티 ID로 채팅방 조회"""
        result = await self._session.execute(
            select(ChatRoom).where(
                and_(ChatRoom.pod_id == pod_id, ChatRoom.is_active == True)
            )
        )
        return result.scalar_one_or_none()

    async def get_chat_room_by_id(self, chat_room_id: int) -> ChatRoom | None:
        """채팅방 ID로 조회"""
        result = await self._session.execute(
            select(ChatRoom).where(
                and_(ChatRoom.id == chat_room_id, ChatRoom.is_active == True)
            )
        )
        return result.scalar_one_or_none()

    # - MARK: 채팅방 업데이트
    async def update_chat_room(
        self, chat_room_id: int, **fields
    ) -> ChatRoom | None:
        """채팅방 정보 업데이트"""
        chat_room = await self.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            return None

        for field, value in fields.items():
            if hasattr(chat_room, field):
                if field == "metadata" and isinstance(value, dict):
                    setattr(chat_room, "room_metadata", json.dumps(value))
                elif field == "room_metadata" and isinstance(value, dict):
                    setattr(chat_room, field, json.dumps(value))
                else:
                    setattr(chat_room, field, value)

        await self._session.flush()
        await self._session.refresh(chat_room)
        return chat_room

    async def update_cover_url(
        self, chat_room_id: int, cover_url: str | None
    ) -> bool:
        """채팅방 커버 이미지 업데이트"""
        chat_room = await self.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            return False

        chat_room.cover_url = cover_url
        await self._session.flush()
        return True

    # - MARK: 채팅방 비활성화 (삭제 대신)
    async def deactivate_chat_room(self, chat_room_id: int) -> bool:
        """채팅방 비활성화"""
        chat_room = await self.get_chat_room_by_id(chat_room_id)
        if not chat_room:
            return False

        chat_room.is_active = False
        await self._session.flush()
        return True

    # - MARK: 멤버 추가
    async def add_member(
        self, chat_room_id: int, user_id: int, role: str = "member"
    ) -> ChatMember:
        """채팅방에 멤버 추가"""
        # 이미 멤버인지 확인
        existing_member = await self.get_member(chat_room_id, user_id)
        if existing_member:
            # 나간 멤버가 다시 들어오는 경우
            if existing_member.left_at:
                existing_member.left_at = None
                existing_member.role = role
                await self._session.flush()
                await self._session.refresh(existing_member)
                return existing_member
            # 이미 참여 중인 경우
            return existing_member

        chat_member = ChatMember(
            chat_room_id=chat_room_id,
            user_id=user_id,
            role=role,
        )
        self._session.add(chat_member)
        await self._session.flush()
        await self._session.refresh(chat_member)
        return chat_member

    # - MARK: 멤버 제거
    async def remove_member(self, chat_room_id: int, user_id: int) -> bool:
        """채팅방에서 멤버 제거 (left_at 설정)"""
        member = await self.get_member(chat_room_id, user_id)
        if not member or member.left_at:
            return False

        from datetime import datetime, timezone

        member.left_at = datetime.now(timezone.utc)
        await self._session.flush()
        return True

    # - MARK: 멤버 조회
    async def get_member(
        self, chat_room_id: int, user_id: int
    ) -> ChatMember | None:
        """채팅방 멤버 조회"""
        result = await self._session.execute(
            select(ChatMember).where(
                and_(
                    ChatMember.chat_room_id == chat_room_id,
                    ChatMember.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_members(self, chat_room_id: int) -> List[ChatMember]:
        """활성 멤버 목록 조회 (left_at이 null인 멤버)"""
        result = await self._session.execute(
            select(ChatMember).where(
                and_(
                    ChatMember.chat_room_id == chat_room_id,
                    ChatMember.left_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_all_members(self, chat_room_id: int) -> List[ChatMember]:
        """모든 멤버 목록 조회 (나간 멤버 포함)"""
        result = await self._session.execute(
            select(ChatMember).where(ChatMember.chat_room_id == chat_room_id)
        )
        return list(result.scalars().all())

    # - MARK: 사용자가 참여한 채팅방 목록 조회
    async def get_user_chat_rooms(self, user_id: int) -> List[ChatRoom]:
        """사용자가 참여한 채팅방 목록 조회"""
        result = await self._session.execute(
            select(ChatRoom)
            .join(ChatMember, ChatRoom.id == ChatMember.chat_room_id)
            .where(
                and_(
                    ChatMember.user_id == user_id,
                    ChatMember.left_at.is_(None),
                    ChatRoom.is_active == True,
                )
            )
        )
        return list(result.scalars().all())
