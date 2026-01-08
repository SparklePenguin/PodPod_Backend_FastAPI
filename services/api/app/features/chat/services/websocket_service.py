import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Set

from app.features.chat.enums import MessageType
from fastapi import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from app.features.chat.schemas.chat_schemas import ChatMessageDto

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # 채널별 연결 관리: {room_id: {user_id: websocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # 사용자별 채널 관리: {user_id: {room_id}}
        self.user_channels: Dict[int, Set[int]] = {}
        # 채널 메타데이터: {room_id: {name, members, data, ...}}
        self.channel_metadata: Dict[int, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        """WebSocket 연결"""
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}

        self.active_connections[room_id][user_id] = websocket

        if user_id not in self.user_channels:
            self.user_channels[user_id] = set()
        self.user_channels[user_id].add(room_id)

        logger.info(f"사용자 {user_id}가 채널 room_id={room_id}에 연결됨")

    def disconnect(self, room_id: int, user_id: int):
        """WebSocket 연결 해제"""
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]

            # 채널에 연결된 사용자가 없으면 채널 제거
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

        if user_id in self.user_channels:
            self.user_channels[user_id].discard(room_id)
            if not self.user_channels[user_id]:
                del self.user_channels[user_id]

        logger.info(f"사용자 {user_id}가 채널 room_id={room_id}에서 연결 해제됨")

    async def send_personal_message(
        self, message: Dict[str, Any], room_id: int, user_id: int
    ):
        """특정 사용자에게 메시지 전송"""
        if (
            room_id in self.active_connections
            and user_id in self.active_connections[room_id]
        ):
            websocket = self.active_connections[room_id][user_id]
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
        room_id: int,
        exclude_user_id: int | None = None,
    ):
        """채널의 모든 사용자에게 메시지 브로드캐스트"""
        if room_id not in self.active_connections:
            return

        disconnected_users = []
        for user_id, websocket in self.active_connections[room_id].items():
            if exclude_user_id and user_id == exclude_user_id:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"브로드캐스트 실패 (user_id={user_id}): {e}")
                disconnected_users.append(user_id)

        # 연결이 끊어진 사용자 제거
        for user_id in disconnected_users:
            self.disconnect(room_id, user_id)

    def get_channel_members(self, room_id: int) -> List[int]:
        """채널의 멤버 목록 조회"""
        if room_id in self.active_connections:
            return list(self.active_connections[room_id].keys())
        return []

    def is_user_in_channel(self, room_id: int, user_id: int) -> bool:
        """사용자가 채널에 있는지 확인"""
        return (
            room_id in self.active_connections
            and user_id in self.active_connections[room_id]
        )


class WebSocketService:
    """WebSocket 기반 채팅 서비스"""

    def __init__(self):
        self.connection_manager = ConnectionManager()

    async def create_channel(
        self,
        room_id: int,
        name: str,
        user_ids: List[int],
        cover_url: str | None = None,
        data: Dict[str, Any | None] = None,
    ) -> Dict[str, Any | None]:
        """
        채널 생성 (메타데이터만 저장, 실제 연결은 WebSocket 연결 시)

        Args:
            room_id: 채팅방 ID
            name: 채널 이름
            user_ids: 초기 멤버 ID 리스트
            cover_url: 커버 이미지 URL
            data: 추가 메타데이터

        Returns:
            생성된 채널 정보
        """
        try:
            # 채널 메타데이터 저장
            self.connection_manager.channel_metadata[room_id] = {
                "room_id": room_id,
                "name": name,
                "cover_url": cover_url or "",
                "data": data or {},
                "members": user_ids,
                "created_at": datetime.now().isoformat(),
            }

            logger.info(f"WebSocket 채널 생성: room_id={room_id}")
            return self.connection_manager.channel_metadata[room_id]

        except Exception as e:
            logger.error(f"WebSocket 채널 생성 실패: {e}")
            return None

    async def get_channel_metadata(self, room_id: int) -> Dict[str, Any | None]:
        """채널 메타데이터 조회"""
        return self.connection_manager.channel_metadata.get(room_id)

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
        self,
        room_id: int,
        user_id: int,
        message: str,
        message_type: MessageType = MessageType.TEXT,
    ) -> bool:
        """메시지 전송"""
        try:
            message_data = {
                "type": message_type.value,
                "room_id": room_id,
                "user_id": user_id,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }

            # 채널의 모든 사용자에게 브로드캐스트 (발신자 포함)
            await self.connection_manager.broadcast_to_channel(
                message_data, room_id, exclude_user_id=None
            )

            logger.info(f"메시지 전송: room_id={room_id}, user_id={user_id}")
            return True

        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            return False

    # - MARK: WebSocket 연결 처리
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        room_id: int,
        user_id: int,
        on_message: Callable[[str, MessageType], None],
    ) -> None:
        """WebSocket 연결 처리 및 메시지 수신 루프"""
        # 채널 메타데이터 확인
        channel_metadata = await self.get_channel_metadata(room_id)
        if not channel_metadata:
            await websocket.close(code=1003)
            logger.warning(f"채널을 찾을 수 없음: room_id={room_id}, user_id={user_id}")
            return

        # 채널 멤버 확인
        members = channel_metadata.get("members", [])
        if user_id not in members:
            await websocket.close(code=1008)
            logger.warning(f"채널 접근 거부: room_id={room_id}, user_id={user_id}")
            return

        # WebSocket 연결
        await self.connection_manager.connect(websocket, room_id, user_id)

        # 연결 알림 전송
        await self.connection_manager.broadcast_to_channel(
            {
                "type": "USER_JOINED",
                "room_id": room_id,
                "user_id": user_id,
                "timestamp": channel_metadata.get("created_at"),
            },
            room_id,
            exclude_user_id=user_id,
        )

        try:
            while True:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_json()

                message_type_str = data.get("type", "TEXT")
                message_type = MessageType(message_type_str)
                message_text = data.get("message", "")

                if message_text:
                    await on_message(message_text, message_type)

        except WebSocketDisconnect:
            # 연결 해제 처리
            self.connection_manager.disconnect(room_id, user_id)

            # 연결 해제 알림 전송
            await self.connection_manager.broadcast_to_channel(
                {
                    "type": "USER_LEFT",
                    "room_id": room_id,
                    "user_id": user_id,
                },
                room_id,
            )

            logger.info(f"사용자 {user_id}가 채널 room_id={room_id}에서 연결 해제됨")

        except Exception as e:
            logger.error(f"WebSocket 오류: {e}")
            self.connection_manager.disconnect(room_id, user_id)
            await websocket.close()

    # - MARK: 메시지 브로드캐스트 (timestamp 파라미터 추가)
    async def broadcast_message(
        self,
        room_id: int,
        user_id: int,
        message: str,
        message_type: MessageType,
        timestamp: str,
    ) -> None:
        """채널의 모든 사용자에게 메시지 브로드캐스트 (레거시)"""
        message_data = {
            "type": message_type.value,
            "room_id": room_id,
            "user_id": user_id,
            "message": message,
            "timestamp": timestamp,
        }
        await self.connection_manager.broadcast_to_channel(
            message_data, room_id, exclude_user_id=None
        )

    # - MARK: 메시지 브로드캐스트 (DTO 전체)
    async def broadcast_message_dto(
        self,
        room_id: int,
        message_dto: "ChatMessageDto",
    ) -> None:
        """채널의 모든 사용자에게 ChatMessageDto 전체를 브로드캐스트"""
        # Pydantic 모델을 JSON 직렬화 가능한 dict로 변환 (camelCase alias 사용)
        message_data = message_dto.model_dump(by_alias=True, mode="json")

        # messageType을 type으로 변경 (중복 제거)
        message_data["type"] = message_data.pop("messageType", "TEXT")

        await self.connection_manager.broadcast_to_channel(
            message_data, room_id, exclude_user_id=None
        )

    # - MARK: 사용자 접속 여부 확인
    def is_user_connected(self, channel_url: str, user_id: int) -> bool:
        """사용자가 채널에 접속 중인지 확인"""
        return self.connection_manager.is_user_in_channel(channel_url, user_id)

    def get_connection_manager(self) -> ConnectionManager:
        """ConnectionManager 인스턴스 반환"""
        return self.connection_manager
