import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # 채널별 연결 관리: {channel_url: {user_id: websocket}}
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}
        # 사용자별 채널 관리: {user_id: {channel_url}}
        self.user_channels: Dict[int, Set[str]] = {}
        # 채널 메타데이터: {channel_url: {name, members, data, ...}}
        self.channel_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, channel_url: str, user_id: int):
        """WebSocket 연결"""
        await websocket.accept()

        if channel_url not in self.active_connections:
            self.active_connections[channel_url] = {}

        self.active_connections[channel_url][user_id] = websocket

        if user_id not in self.user_channels:
            self.user_channels[user_id] = set()
        self.user_channels[user_id].add(channel_url)

        logger.info(f"사용자 {user_id}가 채널 {channel_url}에 연결됨")

    def disconnect(self, channel_url: str, user_id: int):
        """WebSocket 연결 해제"""
        if channel_url in self.active_connections:
            if user_id in self.active_connections[channel_url]:
                del self.active_connections[channel_url][user_id]

            # 채널에 연결된 사용자가 없으면 채널 제거
            if not self.active_connections[channel_url]:
                del self.active_connections[channel_url]

        if user_id in self.user_channels:
            self.user_channels[user_id].discard(channel_url)
            if not self.user_channels[user_id]:
                del self.user_channels[user_id]

        logger.info(f"사용자 {user_id}가 채널 {channel_url}에서 연결 해제됨")

    async def send_personal_message(
        self, message: Dict[str, Any], channel_url: str, user_id: int
    ):
        """특정 사용자에게 메시지 전송"""
        if (
            channel_url in self.active_connections
            and user_id in self.active_connections[channel_url]
        ):
            websocket = self.active_connections[channel_url][user_id]
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"메시지 전송 실패 (user_id={user_id}): {e}")
                return False
        return False

    async def broadcast_to_channel(
        self,
        message: Dict[str, Any],
        channel_url: str,
        exclude_user_id: int | None = None,
    ):
        """채널의 모든 사용자에게 메시지 브로드캐스트"""
        if channel_url not in self.active_connections:
            return

        disconnected_users = []
        for user_id, websocket in self.active_connections[channel_url].items():
            if exclude_user_id and user_id == exclude_user_id:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"브로드캐스트 실패 (user_id={user_id}): {e}")
                disconnected_users.append(user_id)

        # 연결이 끊어진 사용자 제거
        for user_id in disconnected_users:
            self.disconnect(channel_url, user_id)

    def get_channel_members(self, channel_url: str) -> List[int]:
        """채널의 멤버 목록 조회"""
        if channel_url in self.active_connections:
            return list(self.active_connections[channel_url].keys())
        return []

    def is_user_in_channel(self, channel_url: str, user_id: int) -> bool:
        """사용자가 채널에 있는지 확인"""
        return (
            channel_url in self.active_connections
            and user_id in self.active_connections[channel_url]
        )


class WebSocketService:
    """WebSocket 기반 채팅 서비스"""

    def __init__(self):
        self.connection_manager = ConnectionManager()

    async def create_channel(
        self,
        channel_url: str,
        name: str,
        user_ids: List[str],
        cover_url: str | None = None,
        data: Dict[str, Any | None] = None,
    ) -> Dict[str, Any | None]:
        """
        채널 생성 (메타데이터만 저장, 실제 연결은 WebSocket 연결 시)

        Args:
            channel_url: 채널 URL
            name: 채널 이름
            user_ids: 초기 멤버 ID 리스트
            cover_url: 커버 이미지 URL
            data: 추가 메타데이터

        Returns:
            생성된 채널 정보
        """
        try:
            # 채널 메타데이터 저장
            self.connection_manager.channel_metadata[channel_url] = {
                "channel_url": channel_url,
                "name": name,
                "cover_url": cover_url or "",
                "data": data or {},
                "members": [int(uid) for uid in user_ids],
                "created_at": datetime.now().isoformat(),
            }

            logger.info(f"WebSocket 채널 생성: {channel_url}")
            return self.connection_manager.channel_metadata[channel_url]

        except Exception as e:
            logger.error(f"WebSocket 채널 생성 실패: {e}")
            return None

    async def get_channel_metadata(self, channel_url: str) -> Dict[str, Any | None]:
        """채널 메타데이터 조회"""
        return self.connection_manager.channel_metadata.get(channel_url)

    async def update_channel_metadata(
        self, channel_url: str, data: Dict[str, Any]
    ) -> Dict[str, Any | None]:
        """채널 메타데이터 업데이트"""
        if channel_url in self.connection_manager.channel_metadata:
            self.connection_manager.channel_metadata[channel_url].update(data)
            return self.connection_manager.channel_metadata[channel_url]
        return None

    async def update_channel_cover_url(
        self, channel_url: str, cover_url: str
    ) -> Dict[str, Any | None]:
        """채널 커버 이미지 URL 업데이트"""
        return await self.update_channel_metadata(channel_url, {"cover_url": cover_url})

    async def add_members_to_channel(
        self, channel_url: str, user_ids: List[str]
    ) -> bool:
        """채널에 멤버 추가 (메타데이터만 업데이트)"""
        try:
            if channel_url not in self.connection_manager.channel_metadata:
                logger.warning(f"채널이 존재하지 않음: {channel_url}")
                return False

            metadata = self.connection_manager.channel_metadata[channel_url]
            existing_members = set(metadata.get("members", []))
            new_members = [int(uid) for uid in user_ids]

            # 중복 제거하여 추가
            for user_id in new_members:
                existing_members.add(user_id)

            metadata["members"] = list(existing_members)
            logger.info(f"채널 {channel_url}에 멤버 추가: {new_members}")
            return True

        except Exception as e:
            logger.error(f"멤버 추가 실패: {e}")
            return False

    async def remove_member_from_channel(self, channel_url: str, user_id: str) -> bool:
        """채널에서 멤버 제거"""
        try:
            if channel_url not in self.connection_manager.channel_metadata:
                return False

            metadata = self.connection_manager.channel_metadata[channel_url]
            members = metadata.get("members", [])

            user_id_int = int(user_id)
            if user_id_int in members:
                members.remove(user_id_int)
                metadata["members"] = members

                # 연결되어 있으면 연결 해제
                if self.connection_manager.is_user_in_channel(channel_url, user_id_int):
                    self.connection_manager.disconnect(channel_url, user_id_int)

                logger.info(f"채널 {channel_url}에서 멤버 제거: {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"멤버 제거 실패: {e}")
            return False

    async def delete_channel(self, channel_url: str) -> bool:
        """채널 삭제"""
        try:
            # 모든 연결 해제
            if channel_url in self.connection_manager.active_connections:
                user_ids = list(
                    self.connection_manager.active_connections[channel_url].keys()
                )
                for user_id in user_ids:
                    self.connection_manager.disconnect(channel_url, user_id)

            # 메타데이터 삭제
            if channel_url in self.connection_manager.channel_metadata:
                del self.connection_manager.channel_metadata[channel_url]

            logger.info(f"WebSocket 채널 삭제: {channel_url}")
            return True

        except Exception as e:
            logger.error(f"채널 삭제 실패: {e}")
            return False

    async def join_channel(self, channel_url: str, user_ids: List[str]) -> bool:
        """채널에 사용자 참여 (메타데이터 업데이트)"""
        return await self.add_members_to_channel(channel_url, user_ids)

    async def create_user(
        self, user_id: str, nickname: str = "사용자", profile_url: str = ""
    ) -> bool:
        """
        사용자 생성 (WebSocket에서는 메타데이터만 관리)
        실제 사용자 정보는 DB에서 관리하므로 여기서는 성공으로 처리
        """
        logger.info(f"WebSocket 사용자 생성: {user_id}")
        return True

    async def update_user_profile(
        self, user_id: str, nickname: str | None = None, profile_url: str | None = None
    ) -> bool:
        """
        사용자 프로필 업데이트 (WebSocket에서는 메타데이터만 관리)
        실제 사용자 정보는 DB에서 관리하므로 여기서는 성공으로 처리
        """
        logger.info(f"WebSocket 사용자 프로필 업데이트: {user_id}")
        return True

    async def send_message(
        self, channel_url: str, user_id: int, message: str, message_type: str = "MESG"
    ) -> bool:
        """메시지 전송"""
        try:
            message_data = {
                "type": message_type,
                "channel_url": channel_url,
                "user_id": user_id,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }

            # 채널의 모든 사용자에게 브로드캐스트 (발신자 포함)
            await self.connection_manager.broadcast_to_channel(
                message_data, channel_url, exclude_user_id=None
            )

            logger.info(f"메시지 전송: 채널={channel_url}, 사용자={user_id}")
            return True

        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            return False

    def get_connection_manager(self) -> ConnectionManager:
        """ConnectionManager 인스턴스 반환"""
        return self.connection_manager
