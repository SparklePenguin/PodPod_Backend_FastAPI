import json
import logging
from datetime import datetime, time, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse
from app.core.database import get_session
from app.core.services.fcm_service import FCMService
from app.features.pods.repositories.pod_repository import PodCRUD
from app.features.pods.schemas import SimplePodDto
from app.features.users.repositories import UserRepository

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
    request: Request, db: AsyncSession = Depends(get_session)
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
    sender_user_id_raw: str | None = sender.get("user_id") or sender.get("userId")

    # 채널 정보에서 파티 이름 추출
    channel: Dict[str, Any] = payload_body.get("channel", {}) or payload.get(
        "channel", {}
    )
    party_name: str = channel.get("name") or channel.get("channel_url") or "파티"

    # 채널 정보에서 pod_id 추출
    pod_id: int | None = None

    # 1. 채널 URL에서 추출 (pod_{pod_id}_chat 형식)
    channel_url: str | None = channel.get("channel_url")
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
    simple_pod_dict: Dict[str, Any | None] = None
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
                sub_categories_value = getattr(pod, "sub_categories", None)
                if sub_categories_value:
                    try:
                        sub_categories = json.loads(sub_categories_value)
                    except (json.JSONDecodeError, TypeError):
                        sub_categories = []

                # pod 속성을 안전하게 추출
                pod_id_value: int = getattr(pod, "id", 0)
                pod_owner_id: int = getattr(pod, "owner_id", 0)
                pod_title: str = getattr(pod, "title", "")
                pod_thumbnail_url: str | None = getattr(pod, "thumbnail_url", None)
                pod_image_url: str | None = getattr(pod, "image_url", None)
                pod_place: str = getattr(pod, "place", "")
                pod_meeting_date = getattr(pod, "meeting_date", None)
                pod_meeting_time = getattr(pod, "meeting_time", None)

                simple_pod = SimplePodDto(
                    id=pod_id_value,
                    owner_id=pod_owner_id,
                    title=pod_title,
                    thumbnail_url=pod_thumbnail_url or pod_image_url or "",
                    sub_categories=sub_categories,
                    meeting_place=pod_place,
                    meeting_date=_convert_to_timestamp(
                        pod_meeting_date, pod_meeting_time
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
        user_crud = UserRepository(db)

        for rid in recipient_ids:
            user = await user_crud.get_by_id(rid)
            if not user:
                continue
            # fcm_token을 안전하게 추출
            fcm_token: str | None = getattr(user, "fcm_token", None)
            if not fcm_token:
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
                    token=fcm_token,
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
