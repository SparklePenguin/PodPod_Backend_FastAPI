from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional
import logging
import json

from app.core.database import get_db
from app.schemas.common.base_response import BaseResponse
from app.schemas.pod_review import SimplePodDto
from app.services.fcm_service import FCMService
from app.crud.user import UserCRUD
from app.crud.pod.pod import PodCRUD
from datetime import datetime, time, timezone


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

    # 채널 정보에서 파티 이름 추출
    channel: Dict[str, Any] = payload_body.get("channel", {}) or payload.get(
        "channel", {}
    )
    party_name: str = channel.get("name") or channel.get("channel_url") or "파티"

    # 채널 정보에서 pod_id 추출
    pod_id: Optional[int] = None

    # 1. 채널 URL에서 추출 (pod_{pod_id}_chat 형식)
    channel_url: Optional[str] = channel.get("channel_url")
    if channel_url:
        try:
            # pod_123_chat 또는 pod_123_123456789 형식에서 pod_id 추출
            parts = channel_url.split("_")
            if len(parts) >= 2 and parts[0] == "pod":
                pod_id = int(parts[1])
        except (ValueError, IndexError):
            pass

    # 2. 채널 data에서 추출 (JSON 문자열 또는 딕셔너리)
    if not pod_id:
        channel_data = channel.get("data")
        if channel_data:
            try:
                # JSON 문자열인 경우 파싱
                if isinstance(channel_data, str):
                    channel_data = json.loads(channel_data)

                # 딕셔너리에서 id 추출
                if isinstance(channel_data, dict):
                    pod_id = channel_data.get("id")
                    if pod_id:
                        pod_id = int(pod_id)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

    # 발송자 이름 추출
    sender_name: str = (
        sender.get("nickname")
        or sender.get("name")
        or sender.get("user_id")
        or "알 수 없음"
    )

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

    # Pod 정보 조회 (pod_id가 있을 경우)
    simple_pod_dict: Optional[Dict[str, Any]] = None
    if pod_id:
        try:
            pod_crud = PodCRUD(db)
            pod = await pod_crud.get_pod_by_id(pod_id)
            if pod:
                # meeting_date와 meeting_time을 timestamp로 변환 (UTC로 저장된 값이므로 UTC로 해석)
                def _convert_to_timestamp(meeting_date, meeting_time):
                    """date와 time 객체를 UTC로 해석하여 하나의 timestamp로 변환"""
                    if meeting_date is None:
                        return 0
                    if meeting_time is None:
                        dt = datetime.combine(
                            meeting_date, time.min, tzinfo=timezone.utc
                        )
                    else:
                        dt = datetime.combine(
                            meeting_date, meeting_time, tzinfo=timezone.utc
                        )
                    return int(dt.timestamp() * 1000)  # milliseconds

                # sub_categories 파싱
                sub_categories = []
                if pod.sub_categories:
                    try:
                        sub_categories = json.loads(pod.sub_categories)
                    except (json.JSONDecodeError, TypeError):
                        sub_categories = []

                simple_pod = SimplePodDto(
                    id=pod.id,
                    owner_id=pod.owner_id,
                    title=pod.title,
                    thumbnail_url=pod.thumbnail_url or pod.image_url or "",
                    sub_categories=sub_categories,
                    meeting_place=pod.place,
                    meeting_date=_convert_to_timestamp(
                        pod.meeting_date, pod.meeting_time
                    ),
                )
                # SimplePodDto를 JSON 문자열로 변환
                simple_pod_dict = simple_pod.model_dump(mode="json", by_alias=True)
        except Exception as e:
            logger.error(f"Pod 정보 조회 실패: pod_id={pod_id}, error={e}")

    # 알림 전송 (가능한 경우에만)
    notified: List[int] = []
    if recipient_ids and message_text:
        fcm = FCMService()
        user_crud = UserCRUD(db)

        for rid in recipient_ids:
            user = await user_crud.get_by_id(rid)
            if not user or not user.fcm_token:
                continue

            # 제목: 파티 이름
            title = party_name

            # 본문: "발송자 이름: 메시지 내용"
            message_preview = (
                message_text if len(message_text) <= 60 else message_text[:57] + "..."
            )
            body = f"{sender_name}: {message_preview}"

            # 데이터 타입은 커뮤니티/채팅 성격으로 설정
            data = {
                "type": "COMMUNITY",
                "value": "CHAT_MESSAGE_RECEIVED",
                "relatedId": str(pod_id) if pod_id else str(rid),
            }
            # pod 정보 추가 (있을 경우) - JSON 문자열로 변환
            if simple_pod_dict:
                data["pod"] = json.dumps(simple_pod_dict, ensure_ascii=False)
            # channel_url 추가 (있을 경우)
            if channel_url:
                data["channelUrl"] = channel_url
                logger.info(f"[Sendbird 웹훅] channelUrl 추가: {channel_url}")
            else:
                logger.warning(f"[Sendbird 웹훅] channel_url이 없음: {channel}")
            logger.info(f"[Sendbird 웹훅] 최종 data: {data}")
            try:
                await fcm.send_notification(
                    token=user.fcm_token,
                    title=title,
                    body=body,
                    data=data,
                    db=db,
                    user_id=rid,
                    related_user_id=None,
                    related_pod_id=pod_id,
                )
                notified.append(rid)
            except Exception as e:
                logger.error(f"Sendbird 웹훅 알림 전송 실패: user_id={rid}, error={e}")

    return BaseResponse.ok({"processed": True, "notified": notified})
