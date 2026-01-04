from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.providers import get_notification_service
from app.features.notifications.schemas import (
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.features.notifications.services.notification_service import (
    NotificationService,
)
from fastapi import APIRouter, Depends, Query

router = APIRouter()


# - MARK: 알림 목록 조회
@router.get(
    "",
    response_model=BaseResponse[PageDto[NotificationResponse]],
    description="알림 목록 조회 (페이지네이션 지원)",
)
async def get_notifications(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    unread_only: bool = Query(False, description="읽지 않은 알림만 조회할지 여부"),
    category: str | None = Query(
        None, description="카테고리 필터 (pod, community, notice)"
    ),
    current_user_id: int = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    result = await service.get_notifications(
        user_id=current_user_id,
        page=page,
        size=size,
        unread_only=unread_only,
        category=category,
    )
    return BaseResponse.ok(data=result)


# - MARK: 읽지 않은 알림 개수 조회
@router.get(
    "/unread-count",
    response_model=BaseResponse[NotificationUnreadCountResponse],
    description="읽지 않은 알림 개수 조회",
)
async def get_unread_count(
    current_user_id: int = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    result = await service.get_unread_count(current_user_id)
    return BaseResponse.ok(data=result)


# - MARK: 알림 읽음 처리
@router.put(
    "/{notification_id}",
    response_model=BaseResponse[NotificationResponse],
    description="알림 읽음 처리",
)
async def mark_notification_as_read(
    notification_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    notification = await service.mark_as_read(notification_id, current_user_id)
    return BaseResponse.ok(data=notification)


# - MARK: 모든 알림 읽음 처리
@router.put(
    "",
    response_model=BaseResponse[dict],
    description="모든 알림 읽음 처리",
)
async def mark_all_notifications_as_read(
    current_user_id: int = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    result = await service.mark_all_as_read(current_user_id)
    return BaseResponse.ok(data=result)


# - MARK: 알림 삭제
@router.delete(
    "/{notification_id}",
    response_model=BaseResponse[dict],
    description="알림 삭제",
)
async def delete_notification(
    notification_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    result = await service.delete_notification(notification_id, current_user_id)
    return BaseResponse.ok(data=result)


# - MARK: 읽은 알림 전체 삭제
@router.delete(
    "/read",
    response_model=BaseResponse[dict],
    description="읽은 알림 전체 삭제",
)
async def delete_all_read_notifications(
    current_user_id: int = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    result = await service.delete_all_read_notifications(current_user_id)
    return BaseResponse.ok(data=result)
