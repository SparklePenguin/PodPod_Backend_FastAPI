"""
채팅 알림 서비스
FCM 알림 전송 담당
"""

import json
import logging
from typing import List

from app.features.notifications.services.fcm_service import FCMService
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.chat.services.chat_redis_cache_service import ChatRedisCacheService
from app.features.chat.services.websocket_service import ConnectionManager
from app.features.users.repositories import UserRepository
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChatNotificationService:
    """채팅 알림 서비스 - FCM 알림 전송 담당"""

    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        chat_room_repo: ChatRoomRepository,
        fcm_service: FCMService,
        redis: Redis | None = None,
        connection_manager: ConnectionManager | None = None,
    ) -> None:
        """
        Args:
            session: 데이터베이스 세션
            user_repo: 사용자 레포지토리
            chat_room_repo: 채팅방 레포지토리
            fcm_service: FCM 서비스
            redis: Redis 클라이언트 (선택적)
            connection_manager: WebSocket 연결 관리자 (선택적)
        """
        self._session = session
        self._user_repo = user_repo
        self._chat_room_repo = chat_room_repo
        self._redis_cache = ChatRedisCacheService(redis) if redis else None
        self._fcm_service = fcm_service
        self._connection_manager = connection_manager

    # - MARK: 채널 멤버에게 FCM 알림 전송
    async def send_notifications_to_channel(
        self,
        room_id: int,
        sender_id: int,
        sender_name: str,
        message: str,
        pod_id: int | None = None,
        pod_title: str = "파티",
        simple_pod_dict: dict | None = None,
    ) -> None:
        """채널의 모든 멤버에게 FCM 알림 전송 (접속 중이면 제외)"""
        # 채팅방 멤버 조회 (Redis 우선, 없으면 DB)
        member_ids = await self._get_members_with_cache(room_id)
        if not member_ids:
            return

        # 각 멤버에게 알림 전송
        for member_id in member_ids:
            if member_id == sender_id:
                continue  # 발신자 제외

            # 접속 중이면 FCM 전송 안 함 (Redis 우선)
            if await self._is_user_connected(room_id, member_id):
                continue

            await self._send_fcm_notification(
                recipient_id=member_id,
                sender_name=sender_name,
                message=message,
                room_id=room_id,
                pod_id=pod_id,
                pod_title=pod_title,
                simple_pod_dict=simple_pod_dict,
            )

    # - MARK: FCM 알림 전송
    async def _send_fcm_notification(
        self,
        recipient_id: int,
        sender_name: str,
        message: str,
        room_id: int,
        pod_id: int | None = None,
        pod_title: str = "파티",
        simple_pod_dict: dict | None = None,
    ) -> None:
        """FCM 알림 전송 (내부 메서드)"""
        try:
            # 수신자 정보 조회
            recipient = await self._user_repo.get_by_id(recipient_id)
            if not recipient or not recipient.detail or not recipient.detail.fcm_token:
                return

            # 알림 제목: 파티 이름
            title = pod_title

            # 알림 본문: "발송자 이름: 메시지 내용"
            message_preview = message if len(message) <= 60 else message[:57] + "..."
            body = f"{sender_name}: {message_preview}"

            # 알림 데이터
            data = {
                "type": "COMMUNITY",
                "value": "CHAT_MESSAGE_RECEIVED",
                "relatedId": str(pod_id) if pod_id else str(recipient_id),
            }
            if simple_pod_dict:
                data["pod"] = json.dumps(simple_pod_dict, ensure_ascii=False)
            if room_id:
                data["roomId"] = str(room_id)

            # FCM 전송
            await self._fcm_service.send_notification(
                token=recipient.detail.fcm_token,
                title=title,
                body=body,
                data=data,
                db=self._session,
                user_id=recipient_id,
                related_user_id=None,
                related_pod_id=pod_id,
            )
            logger.info(
                f"채팅 메시지 FCM 알림 전송: recipient_id={recipient_id}, room_id={room_id}"
            )

        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: recipient_id={recipient_id}, error={e}")

    # - MARK: Redis 캐시를 활용한 멤버 조회
    async def _get_members_with_cache(self, room_id: int) -> List[int]:
        """채팅방 멤버 조회 (Redis 우선, 없으면 DB 조회 후 캐시)"""
        # Redis에서 먼저 조회
        if self._redis_cache:
            cached_members = await self._redis_cache.get_members(room_id)
            if cached_members is not None:
                return list(cached_members)

        # DB에서 조회
        chat_members = await self._chat_room_repo.get_active_members(room_id)
        member_ids = [m.user_id for m in chat_members]

        # Redis에 캐시
        if self._redis_cache and member_ids:
            await self._redis_cache.set_members(room_id, member_ids)

        return member_ids

    # - MARK: 사용자 접속 상태 확인
    async def _is_user_connected(self, room_id: int, user_id: int) -> bool:
        """사용자가 채팅방에 접속 중인지 확인 (Redis 우선, 없으면 ConnectionManager)"""
        # Redis에서 먼저 확인
        if self._redis_cache:
            if await self._redis_cache.is_user_connected(room_id, user_id):
                return True

        # ConnectionManager에서도 확인 (fallback)
        if self._connection_manager:
            return self._connection_manager.is_user_in_channel(room_id, user_id)

        return False
