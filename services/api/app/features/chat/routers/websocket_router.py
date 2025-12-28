import logging

from app.core.config import settings
from app.core.services.chat_service import ChatService as CoreChatService
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_user_id_from_token(token: str) -> int | None:
    """WebSocket 연결에서 토큰으로 사용자 ID 추출"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        subject = payload.get("sub")
        if subject is None:
            return None
        return int(subject)
    except (JWTError, ValueError, TypeError):
        return None


# - MARK: WebSocket 채팅 연결
@router.websocket("/ws/{channel_url}")
async def websocket_endpoint(
    websocket: WebSocket, channel_url: str, token: str | None = Query(None)
):
    """
    WebSocket 채팅 엔드포인트

    사용법:
    ws://localhost:8000/api/v1/chat/ws/{channel_url}?token={jwt_token}

    메시지 형식:
    {
        "type": "MESG",  # 메시지 타입 (MESG, FILE, IMAGE 등)
        "message": "안녕하세요"
    }
    """
    # WebSocket 사용 여부 확인
    core_chat_service = CoreChatService()
    websocket_service = core_chat_service.get_websocket_service()

    if not websocket_service:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        logger.warning("WebSocket 서비스가 활성화되지 않았습니다.")
        return

    # 토큰 검증
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("WebSocket 연결: 토큰이 제공되지 않음")
        return

    user_id = await get_user_id_from_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("WebSocket 연결: 유효하지 않은 토큰")
        return

    # 채널 메타데이터 확인
    channel_metadata = await websocket_service.get_channel_metadata(channel_url)
    if not channel_metadata:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        logger.warning(f"WebSocket 연결: 채널이 존재하지 않음 - {channel_url}")
        return

    # 채널 멤버 확인
    members = channel_metadata.get("members", [])
    if user_id not in members:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(
            f"WebSocket 연결: 사용자 {user_id}가 채널 {channel_url}의 멤버가 아님"
        )
        return

    # 연결 관리자 가져오기
    connection_manager = websocket_service.get_connection_manager()

    # WebSocket 연결
    await connection_manager.connect(websocket, channel_url, user_id)

    # 연결 알림 전송
    await connection_manager.broadcast_to_channel(
        {
            "type": "USER_JOINED",
            "channel_url": channel_url,
            "user_id": user_id,
            "timestamp": connection_manager.channel_metadata[channel_url].get(
                "created_at"
            ),
        },
        channel_url,
        exclude_user_id=user_id,
    )

    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_json()

            message_type = data.get("type", "MESG")
            message_text = data.get("message", "")

            if not message_text:
                continue

            # 메시지 전송 (Chat Service를 통해 DB 저장 및 FCM 전송)
            from app.core.database import AsyncSessionLocal
            from app.deps.service import get_chat_service

            async with AsyncSessionLocal() as session:
                try:
                    chat_service = get_chat_service(session=session)
                    await chat_service.send_message(
                        channel_url=channel_url,
                        user_id=user_id,
                        message=message_text,
                        message_type=message_type,
                    )
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    logger.error(f"메시지 전송 실패: {e}")
                    raise

    except WebSocketDisconnect:
        # 연결 해제 처리
        connection_manager.disconnect(channel_url, user_id)

        # 연결 해제 알림 전송
        await connection_manager.broadcast_to_channel(
            {
                "type": "USER_LEFT",
                "channel_url": channel_url,
                "user_id": user_id,
            },
            channel_url,
        )

        logger.info(f"사용자 {user_id}가 채널 {channel_url}에서 연결 해제됨")

    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        connection_manager.disconnect(channel_url, user_id)
        await websocket.close()


# - MARK: WebSocket 테스트 연결
@router.websocket("/ws/{channel_url}/test")
async def websocket_test_endpoint(
    websocket: WebSocket,
    channel_url: str,
    user_id: int = Query(..., description="테스트용 사용자 ID"),
):
    """
    WebSocket 테스트 엔드포인트 (인증 없이)
    개발/테스트 목적으로만 사용
    """
    core_chat_service = CoreChatService()
    websocket_service = core_chat_service.get_websocket_service()

    if not websocket_service:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return

    # 채널이 없으면 생성
    channel_metadata = await websocket_service.get_channel_metadata(channel_url)
    if not channel_metadata:
        await websocket_service.create_channel(
            channel_url=channel_url,
            name=f"테스트 채널 {channel_url}",
            user_ids=[str(user_id)],
        )

    connection_manager = websocket_service.get_connection_manager()
    await connection_manager.connect(websocket, channel_url, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "MESG")
            message_text = data.get("message", "")

            if message_text:
                # 메시지 전송 (Chat Service를 통해 DB 저장 및 FCM 전송)
                from app.core.database import AsyncSessionLocal
                from app.deps.service import get_chat_service

                async with AsyncSessionLocal() as session:
                    try:
                        from app.deps.service import get_chat_service
                        chat_service = get_chat_service(session=session)
                        await chat_service.send_message(
                            channel_url=channel_url,
                            user_id=user_id,
                            message=message_text,
                            message_type=message_type,
                        )
                        await session.commit()
                    except Exception as e:
                        await session.rollback()
                        logger.error(f"테스트 메시지 전송 실패: {e}")
                        raise

    except WebSocketDisconnect:
        connection_manager.disconnect(channel_url, user_id)
        logger.info(f"테스트 연결 해제: 사용자 {user_id}, 채널 {channel_url}")
