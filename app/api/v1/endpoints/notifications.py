"""
알림 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_current_user_id, get_db
from app.crud.notification import notification_crud
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationUnreadCountResponse,
)
from app.core.http_status import HttpStatus

router = APIRouter()


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="알림 목록 조회",
    description="사용자의 알림 목록을 조회합니다. 페이지네이션을 지원합니다.",
)
async def get_notifications(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1-100)"),
    unread_only: bool = Query(False, description="읽지 않은 알림만 조회할지 여부"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """알림 목록 조회"""
    skip = (page - 1) * size

    # 알림 목록 조회
    notifications = await notification_crud.get_user_notifications(
        db=db,
        user_id=current_user_id,
        skip=skip,
        limit=size,
        unread_only=unread_only,
    )

    # 전체 개수 및 읽지 않은 개수 조회
    total_count = await notification_crud.get_total_count(
        db=db, user_id=current_user_id
    )
    unread_count = await notification_crud.get_unread_count(
        db=db, user_id=current_user_id
    )

    return NotificationListResponse(
        total=total_count,
        unread_count=unread_count,
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
    summary="읽지 않은 알림 개수 조회",
    description="사용자의 읽지 않은 알림 개수를 조회합니다.",
)
async def get_unread_count(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """읽지 않은 알림 개수 조회"""
    unread_count = await notification_crud.get_unread_count(
        db=db, user_id=current_user_id
    )
    return NotificationUnreadCountResponse(unread_count=unread_count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="알림 읽음 처리",
    description="특정 알림을 읽음 처리합니다.",
)
async def mark_notification_as_read(
    notification_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """알림 읽음 처리"""
    notification = await notification_crud.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user_id,
    )

    if not notification:
        raise HTTPException(
            status_code=HttpStatus.NOT_FOUND,
            detail="알림을 찾을 수 없거나 권한이 없습니다.",
        )

    return NotificationResponse.model_validate(notification)


@router.patch(
    "/read-all",
    summary="모든 알림 읽음 처리",
    description="사용자의 모든 알림을 읽음 처리합니다.",
)
async def mark_all_notifications_as_read(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """모든 알림 읽음 처리"""
    updated_count = await notification_crud.mark_all_as_read(
        db=db,
        user_id=current_user_id,
    )

    return {
        "success": True,
        "message": f"{updated_count}개의 알림을 읽음 처리했습니다.",
        "updated_count": updated_count,
    }


@router.delete(
    "/{notification_id}",
    summary="알림 삭제",
    description="특정 알림을 삭제합니다.",
)
async def delete_notification(
    notification_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """알림 삭제"""
    success = await notification_crud.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user_id,
    )

    if not success:
        raise HTTPException(
            status_code=HttpStatus.NOT_FOUND,
            detail="알림을 찾을 수 없거나 권한이 없습니다.",
        )

    return {
        "success": True,
        "message": "알림이 삭제되었습니다.",
    }


@router.delete(
    "/read/all",
    summary="읽은 알림 전체 삭제",
    description="사용자의 읽은 알림을 모두 삭제합니다.",
)
async def delete_all_read_notifications(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """읽은 알림 전체 삭제"""
    deleted_count = await notification_crud.delete_all_read_notifications(
        db=db,
        user_id=current_user_id,
    )

    return {
        "success": True,
        "message": f"{deleted_count}개의 알림을 삭제했습니다.",
        "deleted_count": deleted_count,
    }
