"""
채팅 서비스 추상화 레이어
Sendbird와 WebSocket을 통합하여 Feature Flag로 전환 가능하도록 구현
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.services.sendbird_service import SendbirdService
from app.core.services.websocket_service import WebSocketService

logger = logging.getLogger(__name__)


class ChatService:
    """채팅 서비스 추상화 레이어 (Sendbird + WebSocket 통합)"""

    def __init__(self):
        self.use_websocket = settings.USE_WEBSOCKET_CHAT

        # 두 서비스 모두 초기화 (Feature Flag로 선택)
        self.sendbird_service: Optional[SendbirdService] = None
        self.websocket_service: Optional[WebSocketService] = None

        try:
            if not self.use_websocket:
                self.sendbird_service = SendbirdService()
                logger.info("Sendbird 서비스 초기화 완료")
            else:
                self.websocket_service = WebSocketService()
                logger.info("WebSocket 서비스 초기화 완료")
        except Exception as e:
            logger.warning(f"채팅 서비스 초기화 중 오류 (무시하고 계속): {e}")

    def _get_service(self):
        """현재 활성화된 서비스 반환"""
        if self.use_websocket:
            if not self.websocket_service:
                self.websocket_service = WebSocketService()
            return self.websocket_service
        else:
            if not self.sendbird_service:
                self.sendbird_service = SendbirdService()
            return self.sendbird_service

    async def create_group_channel(
        self,
        channel_url: str,
        name: str,
        user_ids: List[str],
        cover_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        user_profiles: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """그룹 채널 생성"""
        if self.use_websocket:
            service = self._get_service()
            assert isinstance(service, WebSocketService)
            return await service.create_channel(
                channel_url=channel_url,
                name=name,
                user_ids=user_ids,
                cover_url=cover_url,
                data=data,
            )
        else:
            service = self._get_service()
            assert isinstance(service, SendbirdService)
            return await service.create_group_channel(
                channel_url=channel_url,
                name=name,
                user_ids=user_ids,
                cover_url=cover_url,
                data=data,
                user_profiles=user_profiles,
            )

    async def create_group_channel_with_join(
        self,
        channel_url: str,
        name: str,
        user_ids: List[str],
        cover_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        user_profiles: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """그룹 채널 생성 (자동 참여)"""
        if self.use_websocket:
            # WebSocket은 create_channel에서 자동으로 멤버 추가
            service = self._get_service()
            assert isinstance(service, WebSocketService)
            return await service.create_channel(
                channel_url=channel_url,
                name=name,
                user_ids=user_ids,
                cover_url=cover_url,
                data=data,
            )
        else:
            service = self._get_service()
            assert isinstance(service, SendbirdService)
            return await service.create_group_channel_with_join(
                channel_url=channel_url,
                name=name,
                user_ids=user_ids,
                cover_url=cover_url,
                data=data,
                user_profiles=user_profiles,
            )

    async def get_channel_metadata(self, channel_url: str) -> Optional[Dict[str, Any]]:
        """채널 메타데이터 조회"""
        service = self._get_service()
        return await service.get_channel_metadata(channel_url)

    async def update_channel_metadata(
        self, channel_url: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """채널 메타데이터 업데이트"""
        service = self._get_service()
        return await service.update_channel_metadata(channel_url, data)

    async def update_channel_cover_url(
        self, channel_url: str, cover_url: str
    ) -> Optional[Dict[str, Any]]:
        """채널 커버 이미지 URL 업데이트"""
        service = self._get_service()
        return await service.update_channel_cover_url(channel_url, cover_url)

    async def add_members_to_channel(
        self, channel_url: str, user_ids: List[str]
    ) -> bool:
        """채널에 멤버 추가"""
        service = self._get_service()
        return await service.add_members_to_channel(channel_url, user_ids)

    async def remove_member_from_channel(self, channel_url: str, user_id: str) -> bool:
        """채널에서 멤버 제거"""
        service = self._get_service()
        return await service.remove_member_from_channel(channel_url, user_id)

    async def delete_channel(self, channel_url: str) -> bool:
        """채널 삭제"""
        service = self._get_service()
        return await service.delete_channel(channel_url)

    async def join_channel(self, channel_url: str, user_ids: List[str]) -> bool:
        """채널에 사용자 참여"""
        service = self._get_service()
        return await service.join_channel(channel_url, user_ids)

    async def create_user(
        self, user_id: str, nickname: str = "사용자", profile_url: str = ""
    ) -> bool:
        """사용자 생성"""
        service = self._get_service()
        return await service.create_user(user_id, nickname, profile_url)

    async def update_user_profile(
        self, user_id: str, nickname: str | None = None, profile_url: str | None = None
    ) -> bool:
        """사용자 프로필 업데이트"""
        service = self._get_service()
        return await service.update_user_profile(user_id, nickname, profile_url)

    def get_websocket_service(self) -> Optional[WebSocketService]:
        """WebSocket 서비스 인스턴스 반환 (WebSocket 엔드포인트에서 사용)"""
        if self.use_websocket:
            if not self.websocket_service:
                self.websocket_service = WebSocketService()
            return self.websocket_service
        return None
