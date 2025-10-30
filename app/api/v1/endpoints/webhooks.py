from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional
import logging

from app.core.database import get_db
from app.schemas.common.base_response import BaseResponse
from app.services.fcm_service import FCMService
from app.crud.user import UserCRUD


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/sendbird",
    response_model=BaseResponse[dict],
    tags=["webhooks"],
    summary="Sendbird 웹훅 처리",
    description="Sendbird 그룹 채널 메시지 전송 웹훅을 처리합니다.",
)
async def handle_sendbird_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BaseResponse[dict]:
    """Sendbird 그룹 채널 메시지 전송 웹훅 처리 엔드포인트.

    외부 인증 없이 호출되므로, 본문 payload를 안전하게 파싱하고 필수 필드만 사용합니다.
    """
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        # 본문 파싱 실패 시에도 200 OK로 응답 (Sendbird 재시도 방지)
        return BaseResponse.ok({"processed": False})

    category: str = payload.get("category", "")
    if category != "group_channel:message_send":
        # 다른 이벤트는 무시
        return BaseResponse.ok({"processed": True, "ignored": True})

    # 필수 정보 추출 (최대한 방어적으로 처리)
    payload_body: Dict[str, Any] = payload.get("payload", {})
    sender: Dict[str, Any] = payload.get("sender", {}) or payload_body.get("sender", {})
    sender_user_id_raw: Optional[str] = sender.get("user_id") or sender.get("userId")
    message_text: str = payload_body.get("message") or payload_body.get("data", {}).get(
        "message", ""
    )

    # 수신자 후보: 멤버 중에서 보낸 사람 제외
    members: List[Dict[str, Any]] = (
        payload_body.get("members") or payload.get("members") or []
    )
    recipient_ids: List[int] = []
    for m in members:
        uid_raw = m.get("user_id") or m.get("userId")
        if not uid_raw or uid_raw == sender_user_id_raw:
            continue
        try:
            # 우리 서비스의 user.id와 동일하다고 가정 (숫자형 문자열)
            recipient_ids.append(int(uid_raw))
        except (TypeError, ValueError):
            # 매핑 불가 사용자는 건너뜀
            continue

    # 알림 전송 (가능한 경우에만)
    notified: List[int] = []
    if recipient_ids and message_text:
        fcm = FCMService()
        user_crud = UserCRUD(db)

        for rid in recipient_ids:
            user = await user_crud.get_by_id(rid)
            if not user or not user.fcm_token:
                continue
            title = "새 메시지"
            body = (
                message_text if len(message_text) <= 80 else message_text[:77] + "..."
            )
            # 데이터 타입은 커뮤니티/채팅 성격으로 설정
            data = {"type": "COMMUNITY", "value": "CHAT_MESSAGE", "relatedId": str(rid)}
            try:
                await fcm.send_notification(
                    token=user.fcm_token,
                    title=title,
                    body=body,
                    data=data,
                    db=db,
                    user_id=rid,
                    related_user_id=None,
                    related_pod_id=None,
                )
                notified.append(rid)
            except Exception as e:
                logger.error(f"Sendbird 웹훅 알림 전송 실패: user_id={rid}, error={e}")

    return BaseResponse.ok({"processed": True, "notified": notified})
