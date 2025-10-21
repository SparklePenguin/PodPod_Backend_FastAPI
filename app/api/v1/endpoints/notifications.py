"""
알림 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math

from app.api.deps import get_current_user_id, get_db
from app.crud.notification import notification_crud
from app.schemas.notification import (
    NotificationResponse,
    NotificationUnreadCountResponse,
    get_notification_main_type,
)
from app.schemas.common.page_dto import PageDto
from app.schemas.common.base_response import BaseResponse
from app.schemas.follow import SimpleUserDto
from app.schemas.pod.pod_dto import PodDto
from app.core.http_status import HttpStatus
from app.services.pod.pod_service import PodService
from app.services.tendency_service import TendencyService

router = APIRouter()


@router.get(
    "",
    response_model=BaseResponse[PageDto[NotificationResponse]],
    summary="알림 목록 조회",
    description="사용자의 알림 목록을 조회합니다. 페이지네이션을 지원합니다.",
)
async def get_notifications(
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
    unread_only: bool = Query(False, description="읽지 않은 알림만 조회할지 여부"),
    category: Optional[str] = Query(
        None, description="카테고리 필터 (pod, community, notice)"
    ),
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
        category=category,
    )

    # 전체 개수 조회 (unread_only, category 고려)
    total_count = await notification_crud.get_total_count(
        db=db, user_id=current_user_id, unread_only=unread_only, category=category
    )

    # 총 페이지 수 계산
    total_pages = math.ceil(total_count / size) if total_count > 0 else 0

    # DTO 변환 (related_user, related_pod 정보 포함)
    notification_dtos = []
    pod_service = PodService(db)
    tendency_service = TendencyService(db)

    for n in notifications:
        # related_user DTO 생성
        related_user_dto = None
        if n.related_user:
            # 사용자의 성향 정보 조회
            user_tendency = await tendency_service.get_user_tendency_result(
                n.related_user.id
            )
            tendency_type = user_tendency.tendency_type if user_tendency else ""

            related_user_dto = SimpleUserDto(
                id=n.related_user.id,
                nickname=n.related_user.nickname,
                profile_image=n.related_user.profile_image,
                intro=n.related_user.intro or "",
                tendency_type=tendency_type,
                is_following=False,  # TODO: 필요시 조회
            )

        # related_pod DTO 생성
        related_pod_dto = None
        if n.related_pod:
            # SimplePodDto로 변환
            from app.schemas.pod_review import SimplePodDto
            from datetime import datetime, date, time

            # meeting_date와 meeting_time을 하나의 timestamp로 변환
            meeting_timestamp = 0
            if n.related_pod.meeting_date and n.related_pod.meeting_time:
                try:
                    dt = datetime.combine(
                        n.related_pod.meeting_date, n.related_pod.meeting_time
                    )
                    meeting_timestamp = int(dt.timestamp() * 1000)  # milliseconds
                except:
                    meeting_timestamp = 0

            # sub_categories를 문자열에서 리스트로 파싱
            sub_categories_list = []
            if n.related_pod.sub_categories:
                try:
                    import json

                    # 이미 리스트인 경우 그대로 사용, 문자열인 경우 JSON 파싱
                    if isinstance(n.related_pod.sub_categories, list):
                        sub_categories_list = n.related_pod.sub_categories
                    else:
                        sub_categories_list = json.loads(n.related_pod.sub_categories)
                except (json.JSONDecodeError, TypeError, AttributeError):
                    sub_categories_list = []

            related_pod_dto = SimplePodDto(
                id=n.related_pod.id,
                title=n.related_pod.title,
                image_url=n.related_pod.image_url or "",
                sub_categories=sub_categories_list,
                meeting_place=n.related_pod.place or "",
                meeting_date=meeting_timestamp,
            )

        # related_id를 int로 변환 (None이면 None 유지)
        related_id_int = None
        if n.related_id is not None:
            try:
                related_id_int = int(n.related_id)
            except (ValueError, TypeError):
                related_id_int = None

        noti_dict = {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "type": get_notification_main_type(n.notification_type),
            "value": n.notification_value,
            "related_id": related_id_int,
            "category": n.category,
            "is_read": n.is_read,
            "read_at": n.read_at,
            "created_at": n.created_at,
            "related_user": related_user_dto,
            "related_pod": related_pod_dto,
        }
        notification_dtos.append(NotificationResponse.model_validate(noti_dict))

    # PageDto 생성
    page_dto = PageDto[NotificationResponse](
        items=notification_dtos,
        current_page=page,
        page_size=size,
        total_count=total_count,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    return BaseResponse.ok(
        data=page_dto, message_ko="알림 목록 조회 성공", http_status=HttpStatus.OK
    )


@router.get(
    "/unread-count",
    response_model=BaseResponse[NotificationUnreadCountResponse],
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
    return BaseResponse.ok(
        data=NotificationUnreadCountResponse(unread_count=unread_count),
        message_ko="읽지 않은 알림 개수 조회 성공",
        http_status=HttpStatus.OK,
    )


@router.put(
    "/{notification_id}",
    response_model=BaseResponse[NotificationResponse],
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

    return BaseResponse.ok(
        data=NotificationResponse.model_validate(notification),
        message_ko="알림을 읽음 처리했습니다.",
        http_status=HttpStatus.OK,
    )


@router.put(
    "",
    response_model=BaseResponse[dict],
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

    return BaseResponse.ok(
        data={"updatedCount": updated_count},
        message_ko=f"{updated_count}개의 알림을 읽음 처리했습니다.",
        http_status=HttpStatus.OK,
    )


@router.delete(
    "/{notification_id}",
    response_model=BaseResponse[dict],
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

    return BaseResponse.ok(
        data={"success": True},
        message_ko="알림이 삭제되었습니다.",
        http_status=HttpStatus.OK,
    )


@router.delete(
    "/read",
    response_model=BaseResponse[dict],
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

    return BaseResponse.ok(
        data={"deletedCount": deleted_count},
        message_ko=f"{deleted_count}개의 알림을 삭제했습니다.",
        http_status=HttpStatus.OK,
    )
