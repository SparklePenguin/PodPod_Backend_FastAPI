"""
알림 API 엔드포인트
"""

import logging
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.common.schemas import BaseResponse, PageDto
from app.core.http_status import HttpStatus
from app.features.follow.schemas import SimpleUserDto
from app.features.notifications.repositories.notification import (
    notification_crud,
)
from app.features.notifications.repositories.notification_repository import (
    NotificationResponse,
    NotificationUnreadCountResponse,
    get_notification_main_type,
)
from app.features.tendencies.services.tendency_service import TendencyService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=BaseResponse[PageDto[NotificationResponse]],
    summary="알림 목록 조회",
    description="사용자의 알림 목록을 조회합니다. 페이지네이션을 지원합니다.",
)
async def get_notifications(
    page: int = Query(
        1, ge=1, serialization_alias="page", description="페이지 번호 (1부터 시작)"
    ),
    size: int = Query(
        20, ge=1, le=100, serialization_alias="size", description="페이지 크기 (1~100)"
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

    # category를 대문자로 변환 (DB에는 대문자로 저장됨)
    category_upper = category.upper() if category else None

    # 알림 목록 조회
    notifications = await notification_crud.get_user_notifications(
        db=db,
        user_id=current_user_id,
        skip=skip,
        limit=size,
        unread_only=unread_only,
        category=category_upper,
    )

    # 전체 개수 조회 (unread_only, category 고려)
    total_count = await notification_crud.get_total_count(
        db=db, user_id=current_user_id, unread_only=unread_only, category=category_upper
    )

    # 총 페이지 수 계산
    total_pages = math.ceil(total_count / size) if total_count > 0 else 0

    # DTO 변환 (related_user, related_pod 정보 포함)
    notification_dtos = []
    tendency_service = TendencyService(db)

    for n in notifications:
        # related_user DTO 생성
        related_user_dto = None
        if n.related_user:
            # 사용자의 성향 정보 조회 (에러 처리 포함)
            tendency_type = ""
            try:
                user_tendency = await tendency_service.get_user_tendency_result(
                    n.related_user.id
                )
                tendency_type = user_tendency.tendency_type if user_tendency else ""
            except Exception as e:
                logger.warning(
                    f"사용자 성향 정보 조회 실패 (user_id: {n.related_user.id}): {e}"
                )
                tendency_type = ""

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
            from datetime import datetime

            from app.features.pods.schemas import SimplePodDto

            # meeting_date와 meeting_time을 하나의 timestamp로 변환 (UTC로 저장된 값이므로 UTC로 해석)
            meeting_timestamp = 0
            if n.related_pod.meeting_date and n.related_pod.meeting_time:
                try:
                    from datetime import timezone

                    dt = datetime.combine(
                        n.related_pod.meeting_date,
                        n.related_pod.meeting_time,
                        tzinfo=timezone.utc,
                    )
                    meeting_timestamp = int(dt.timestamp() * 1000)  # milliseconds
                except (ValueError, TypeError, AttributeError):
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
                owner_id=n.related_pod.owner_id,
                title=n.related_pod.title,
                thumbnail_url=n.related_pod.thumbnail_url
                or n.related_pod.image_url
                or "",
                sub_categories=sub_categories_list,
                meeting_place=n.related_pod.place or "",
                meeting_date=meeting_timestamp,
            )

        # related_id를 int로 변환 (None이면 None 유지)
        related_id_int: int | None = None
        related_id_value = getattr(n, "related_id", None)
        if related_id_value is not None:
            try:
                related_id_int = int(related_id_value)
            except (ValueError, TypeError):
                related_id_int = None

        # NotificationResponse 직접 생성 (MissingGreenlet 오류 방지)
        # 모델 인스턴스의 실제 값에 접근하기 위해 getattr 사용
        notification_dto = NotificationResponse(
            id=getattr(n, "id"),
            title=getattr(n, "title"),
            body=getattr(n, "body"),
            type=get_notification_main_type(getattr(n, "notification_type")),
            value=getattr(n, "notification_value"),
            related_id=related_id_int,
            category=getattr(n, "category"),
            is_read=getattr(n, "is_read"),
            read_at=getattr(n, "read_at"),
            created_at=getattr(n, "created_at"),
            related_user=related_user_dto,
            related_pod=related_pod_dto,
        )
        notification_dtos.append(notification_dto)

    # PageDto 생성
    page_dto = PageDto[NotificationResponse](
        items=notification_dtos,
        current_page=page,
        size=size,
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

    # NotificationResponse 직접 생성 (MissingGreenlet 오류 방지)
    related_user_dto = None
    if notification.related_user:
        related_user_dto = SimpleUserDto(
            id=notification.related_user.id,
            nickname=notification.related_user.nickname,
            profile_image=notification.related_user.profile_image,
            intro=notification.related_user.intro or "",
            tendency_type="",  # TODO: 필요시 조회
            is_following=False,
        )

    related_pod_dto = None
    if notification.related_pod:
        from datetime import datetime

        from app.features.pods.schemas import SimplePodDto

        # meeting_date와 meeting_time을 하나의 timestamp로 변환 (UTC로 저장된 값이므로 UTC로 해석)
        meeting_timestamp = 0
        if (
            notification.related_pod.meeting_date
            and notification.related_pod.meeting_time
        ):
            try:
                from datetime import timezone

                dt = datetime.combine(
                    notification.related_pod.meeting_date,
                    notification.related_pod.meeting_time,
                    tzinfo=timezone.utc,
                )
                meeting_timestamp = int(dt.timestamp() * 1000)  # milliseconds
            except (ValueError, TypeError, AttributeError):
                meeting_timestamp = 0

        # sub_categories를 문자열에서 리스트로 파싱
        sub_categories_list = []
        if notification.related_pod.sub_categories:
            try:
                import json

                if isinstance(notification.related_pod.sub_categories, list):
                    sub_categories_list = notification.related_pod.sub_categories
                else:
                    sub_categories_list = json.loads(
                        notification.related_pod.sub_categories
                    )
            except (json.JSONDecodeError, TypeError, AttributeError):
                sub_categories_list = []

        related_pod_dto = SimplePodDto(
            id=notification.related_pod.id,
            owner_id=notification.related_pod.owner_id,
            title=notification.related_pod.title,
            thumbnail_url=notification.related_pod.thumbnail_url
            or notification.related_pod.image_url
            or "",
            sub_categories=sub_categories_list,
            meeting_place=notification.related_pod.place or "",
            meeting_date=meeting_timestamp,
        )

    # related_id를 int로 변환
    related_id_int: int | None = None
    related_id_value = getattr(notification, "related_id", None)
    if related_id_value is not None:
        try:
            related_id_int = int(related_id_value)
        except (ValueError, TypeError):
            related_id_int = None

    # 모델 인스턴스의 실제 값에 접근하기 위해 getattr 사용
    notification_dto = NotificationResponse(
        id=getattr(notification, "id"),
        title=getattr(notification, "title"),
        body=getattr(notification, "body"),
        type=get_notification_main_type(getattr(notification, "notification_type")),
        value=getattr(notification, "notification_value"),
        related_id=related_id_int,
        category=getattr(notification, "category"),
        is_read=getattr(notification, "is_read"),
        read_at=getattr(notification, "read_at"),
        created_at=getattr(notification, "created_at"),
        related_user=related_user_dto,
        related_pod=related_pod_dto,
    )

    return BaseResponse.ok(
        data=notification_dto,
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
