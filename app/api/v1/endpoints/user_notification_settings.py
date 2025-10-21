"""
사용자 알림 설정 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_current_user_id, get_db
from app.crud.user_notification_settings import UserNotificationSettingsCRUD
from app.schemas.user_notification_settings import (
    UserNotificationSettingsDto,
    UpdateUserNotificationSettingsRequest,
)
from app.schemas.common.base_response import BaseResponse
from app.core.http_status import HttpStatus

router = APIRouter()


@router.get(
    "",
    response_model=BaseResponse[UserNotificationSettingsDto],
    summary="알림 설정 조회",
    description="사용자의 알림 설정을 조회합니다.",
)
async def get_notification_settings(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """알림 설정 조회"""
    crud = UserNotificationSettingsCRUD(db)

    # 사용자 설정 조회
    settings = await crud.get_by_user_id(current_user_id)

    if not settings:
        # 설정이 없으면 기본 설정 생성
        settings = await crud.create_default_settings(current_user_id)

    # DTO 변환
    settings_dto = UserNotificationSettingsDto(
        id=settings.id,
        user_id=settings.user_id,
        wake_up_alarm=settings.notice_enabled,
        bus_alert=settings.chat_enabled,
        party_alert=settings.pod_enabled,
        community_alert=settings.community_enabled,
        product_alarm=settings.marketing_enabled,
        do_not_disturb_enabled=settings.do_not_disturb_enabled,
        start_time=(
            settings.do_not_disturb_start.strftime("%p %I:%M")
            if settings.do_not_disturb_start
            else None
        ),
        end_time=(
            settings.do_not_disturb_end.strftime("%p %I:%M")
            if settings.do_not_disturb_end
            else None
        ),
        marketing_enabled=settings.marketing_enabled,
    )

    return BaseResponse.ok(
        data=settings_dto,
        message_ko="알림 설정을 조회했습니다.",
        http_status=HttpStatus.OK,
    )


@router.patch(
    "",
    response_model=BaseResponse[UserNotificationSettingsDto],
    summary="알림 설정 수정",
    description="사용자의 알림 설정을 수정합니다. 원하는 필드만 수정할 수 있습니다.",
)
async def update_notification_settings(
    update_data: UpdateUserNotificationSettingsRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """알림 설정 수정"""
    crud = UserNotificationSettingsCRUD(db)

    # 기존 설정 확인
    settings = await crud.get_by_user_id(current_user_id)
    if not settings:
        # 설정이 없으면 기본 설정 생성
        settings = await crud.create_default_settings(current_user_id)

    # 설정 업데이트
    updated_settings = await crud.update_settings(current_user_id, update_data)
    if not updated_settings:
        raise HTTPException(status_code=404, detail="알림 설정을 찾을 수 없습니다.")

    # DTO 변환
    settings_dto = UserNotificationSettingsDto(
        id=updated_settings.id,
        user_id=updated_settings.user_id,
        wake_up_alarm=updated_settings.notice_enabled,
        bus_alert=updated_settings.chat_enabled,
        party_alert=updated_settings.pod_enabled,
        community_alert=updated_settings.community_enabled,
        product_alarm=updated_settings.marketing_enabled,
        do_not_disturb_enabled=updated_settings.do_not_disturb_enabled,
        start_time=(
            updated_settings.do_not_disturb_start.strftime("%p %I:%M")
            if updated_settings.do_not_disturb_start
            else None
        ),
        end_time=(
            updated_settings.do_not_disturb_end.strftime("%p %I:%M")
            if updated_settings.do_not_disturb_end
            else None
        ),
        marketing_enabled=updated_settings.marketing_enabled,
    )

    return BaseResponse.ok(
        data=settings_dto,
        message_ko="알림 설정을 수정했습니다.",
        http_status=HttpStatus.OK,
    )
