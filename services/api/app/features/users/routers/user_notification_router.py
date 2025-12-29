from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.service import get_user_notification_service
from app.features.users.schemas import (
    UpdateUserNotificationSettingsRequest,
    UserNotificationSettingsDto,
)
from app.features.users.services.user_notification_service import (
    UserNotificationService,
)
from fastapi import APIRouter, Depends, status

router = APIRouter()


# - MARK: 알림 설정 조회
@router.get(
    "",
    response_model=BaseResponse[UserNotificationSettingsDto],
    description="사용자의 알림 설정을 조회합니다.",
)
async def get_notification_settings(
    current_user_id: int = Depends(get_current_user_id),
    service: UserNotificationService = Depends(get_user_notification_service),
):
    settings_dto = await service.get_notification_settings(current_user_id)

    return BaseResponse.ok(
        data=settings_dto,
        message_ko="알림 설정을 조회했습니다.",
        http_status=status.HTTP_200_OK,
    )


# - MARK: 알림 설정 수정
@router.patch(
    "",
    response_model=BaseResponse[UserNotificationSettingsDto],
    description="사용자 알림 설정 수정",
)
async def update_notification_settings(
    update_data: UpdateUserNotificationSettingsRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: UserNotificationService = Depends(get_user_notification_service),
):
    settings_dto = await service.update_notification_settings(
        current_user_id, update_data
    )

    return BaseResponse.ok(
        data=settings_dto,
        message_ko="알림 설정을 수정했습니다.",
        http_status=status.HTTP_200_OK,
    )
