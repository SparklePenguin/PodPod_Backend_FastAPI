import logging

from app.core.config import settings
from app.features.chat.services.websocket_service import WebSocketService
from fastapi import APIRouter, Query, WebSocket, status
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
    websocket: WebSocket,
    channel_url: str,
    token: str | None = Query(None),
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

    # Chat UseCase를 통해 WebSocket 연결 처리
    from app.core.database import AsyncSessionLocal
    from app.deps.providers import get_chat_use_case

    async with AsyncSessionLocal() as session:
        chat_use_case = get_chat_use_case(session=session)
        await chat_use_case.handle_websocket_connection(
            websocket=websocket,
            channel_url=channel_url,
            user_id=user_id,
        )


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
    from app.core.database import AsyncSessionLocal

    websocket_service = WebSocketService()

    # 채널이 없으면 생성
    channel_metadata = await websocket_service.get_channel_metadata(channel_url)
    if not channel_metadata:
        await websocket_service.create_channel(
            channel_url=channel_url,
            name=f"테스트 채널 {channel_url}",
            user_ids=[str(user_id)],
        )

    # Chat UseCase를 통해 WebSocket 연결 처리
    from app.deps.providers import get_chat_use_case

    async with AsyncSessionLocal() as session:
        chat_use_case = get_chat_use_case(session=session)
        await chat_use_case.handle_websocket_connection(
            websocket=websocket,
            channel_url=channel_url,
            user_id=user_id,
        )
