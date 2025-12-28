"""
채팅 WebSocket 서비스
WebSocket 브로드캐스트 담당
"""

import logging

from app.core.services.websocket_service import ConnectionManager, WebSocketService

logger = logging.getLogger(__name__)


class ChatWebSocketService:
    """채팅 WebSocket 서비스 - WebSocket 브로드캐스트 담당"""

    def __init__(
        self,
        websocket_service: WebSocketService | None = None,
    ):
        self._websocket_service = websocket_service
        self._connection_manager: ConnectionManager | None = None
        if websocket_service:
            self._connection_manager = websocket_service.get_connection_manager()

    # - MARK: 메시지 브로드캐스트
    async def broadcast_message(
        self,
        channel_url: str,
        user_id: int,
        message: str,
        message_type: str,
        timestamp: str,
    ) -> None:
        """채널의 모든 사용자에게 메시지 브로드캐스트"""
        if not self._connection_manager:
            logger.warning("ConnectionManager가 없어 브로드캐스트를 할 수 없습니다.")
            return

        message_data = {
            "type": message_type,
            "channel_url": channel_url,
            "user_id": user_id,
            "message": message,
            "timestamp": timestamp,
        }
        await self._connection_manager.broadcast_to_channel(
            message_data, channel_url, exclude_user_id=None
        )

    # - MARK: 채널 메타데이터 조회
    async def get_channel_metadata(self, channel_url: str) -> dict | None:
        """채널 메타데이터 조회"""
        if not self._websocket_service:
            return None
        return await self._websocket_service.get_channel_metadata(channel_url)

    # - MARK: 사용자 접속 여부 확인
    def is_user_connected(self, channel_url: str, user_id: int) -> bool:
        """사용자가 채널에 접속 중인지 확인"""
        if not self._connection_manager:
            return False
        return self._connection_manager.is_user_in_channel(channel_url, user_id)

    # - MARK: ConnectionManager 반환
    def get_connection_manager(self) -> ConnectionManager | None:
        """ConnectionManager 반환"""
        return self._connection_manager
