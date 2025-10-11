"""
알림 설정 API 엔드포인트
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.crud.user_notification_settings import user_notification_settings_crud
from app.schemas.user_notification_settings import (
    NotificationSettingsResponse,
    UpdateNotificationSettingsRequest,
)
from app.schemas.common.base_response import BaseResponse
from app.core.http_status import HttpStatus

router = APIRouter()


@router.get(
    "",
    response_model=BaseResponse[NotificationSettingsResponse],
    summary="알림 설정 조회",
    description="사용자의 알림 설정을 조회합니다.",
)
async def get_notification_settings(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """알림 설정 조회"""
    settings = await user_notification_settings_crud.get_or_create(db, current_user_id)

    # time 객체를 "HH:MM" 문자열로 변환
    settings_dict = {
        "notice_enabled": settings.notice_enabled,
        "pod_enabled": settings.pod_enabled,
        "community_enabled": settings.community_enabled,
        "chat_enabled": settings.chat_enabled,
        "do_not_disturb_enabled": settings.do_not_disturb_enabled,
        "do_not_disturb_start": (
            settings.do_not_disturb_start.strftime("%H:%M")
            if settings.do_not_disturb_start
            else None
        ),
        "do_not_disturb_end": (
            settings.do_not_disturb_end.strftime("%H:%M")
            if settings.do_not_disturb_end
            else None
        ),
        "marketing_enabled": settings.marketing_enabled,
    }

    return BaseResponse.ok(
        data=NotificationSettingsResponse.model_validate(settings_dict),
        message_ko="알림 설정 조회 성공",
        http_status=HttpStatus.OK,
    )


@router.put(
    "",
    response_model=BaseResponse[NotificationSettingsResponse],
    summary="알림 설정 업데이트",
    description="사용자의 알림 설정을 업데이트합니다. 제공된 필드만 업데이트됩니다.",
)
async def update_notification_settings(
    request: UpdateNotificationSettingsRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """알림 설정 업데이트"""
    settings = await user_notification_settings_crud.update_settings(
        db=db,
        user_id=current_user_id,
        notice_enabled=request.notice_enabled,
        pod_enabled=request.pod_enabled,
        community_enabled=request.community_enabled,
        chat_enabled=request.chat_enabled,
        do_not_disturb_enabled=request.do_not_disturb_enabled,
        do_not_disturb_start=request.do_not_disturb_start,
        do_not_disturb_end=request.do_not_disturb_end,
        marketing_enabled=request.marketing_enabled,
    )

    # time 객체를 "HH:MM" 문자열로 변환
    settings_dict = {
        "notice_enabled": settings.notice_enabled,
        "pod_enabled": settings.pod_enabled,
        "community_enabled": settings.community_enabled,
        "chat_enabled": settings.chat_enabled,
        "do_not_disturb_enabled": settings.do_not_disturb_enabled,
        "do_not_disturb_start": (
            settings.do_not_disturb_start.strftime("%H:%M")
            if settings.do_not_disturb_start
            else None
        ),
        "do_not_disturb_end": (
            settings.do_not_disturb_end.strftime("%H:%M")
            if settings.do_not_disturb_end
            else None
        ),
        "marketing_enabled": settings.marketing_enabled,
    }

    return BaseResponse.ok(
        data=NotificationSettingsResponse.model_validate(settings_dict),
        message_ko="알림 설정이 업데이트되었습니다.",
        http_status=HttpStatus.OK,
    )
