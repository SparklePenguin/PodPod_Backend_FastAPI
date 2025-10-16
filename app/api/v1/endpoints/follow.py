from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.api.deps import get_db, get_current_user_id
from app.services.follow_service import FollowService
from app.schemas.follow import (
    FollowRequest,
    FollowResponse,
    FollowListResponse,
    FollowStatsResponse,
    SimpleUserDto,
    FollowNotificationStatusResponse,
    FollowNotificationUpdateRequest,
)
from app.schemas.pod.pod_dto import PodDto
from app.schemas.common.page_dto import PageDto
from app.schemas.common.base_response import BaseResponse
from app.core.http_status import HttpStatus
from app.core.error_codes import get_error_info

router = APIRouter()


@router.post("/", response_model=BaseResponse[FollowResponse])
async def follow_user(
    request: FollowRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """사용자 팔로우"""
    try:
        follow_service = FollowService(db)
        follow = await follow_service.follow_user(
            follower_id=current_user_id, following_id=request.following_id
        )

        return BaseResponse.ok(
            data=follow,
            http_status=HttpStatus.CREATED,
            message_ko="팔로우가 완료되었습니다.",
            message_en="Successfully followed the user.",
        )
    except ValueError as e:
        return BaseResponse(
            data=None,
            http_status=400,
            message_ko=str(e),
            message_en="Failed to follow user.",
            error="FOLLOW_FAILED",
            error_code=4002,
            dev_note=None,
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="팔로우 중 오류가 발생했습니다.",
            message_en="An error occurred while following the user.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.delete("/{following_id}", response_model=BaseResponse[bool])
async def unfollow_user(
    following_id: int = Path(..., description="팔로우 취소할 사용자 ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """사용자 팔로우 취소"""
    try:
        follow_service = FollowService(db)
        success = await follow_service.unfollow_user(
            follower_id=current_user_id, following_id=following_id
        )

        if not success:
            return BaseResponse(
                data=None,
                http_status=404,
                message_ko="팔로우 관계를 찾을 수 없습니다.",
                message_en="Follow relationship not found.",
                error="FOLLOW_NOT_FOUND",
                error_code=4001,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=success,
            http_status=HttpStatus.OK,
            message_ko="팔로우가 취소되었습니다.",
            message_en="Successfully unfollowed the user.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=error_info.http_status,
            message_ko="팔로우 취소 중 오류가 발생했습니다.",
            message_en="An error occurred while unfollowing the user.",
        )


@router.get("/followings", response_model=BaseResponse[PageDto[SimpleUserDto]])
async def get_following_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """팔로우하는 사용자 목록 조회"""
    try:
        follow_service = FollowService(db)
        following_list = await follow_service.get_following_list(
            user_id=current_user_id, page=page, size=size
        )

        return BaseResponse.ok(
            data=following_list,
            http_status=HttpStatus.OK,
            message_ko="팔로우 목록을 조회했습니다.",
            message_en="Successfully retrieved following list.",
        )
    except Exception as e:
        import traceback

        print(f"팔로우 목록 조회 오류: {e}")
        traceback.print_exc()
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="팔로우 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving following list.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.get("/followers", response_model=BaseResponse[PageDto[SimpleUserDto]])
async def get_followers_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """팔로워 목록 조회"""
    try:
        follow_service = FollowService(db)
        followers_list = await follow_service.get_followers_list(
            user_id=current_user_id,
            current_user_id=current_user_id,
            page=page,
            size=size,
        )

        return BaseResponse.ok(
            data=followers_list,
            http_status=HttpStatus.OK,
            message_ko="팔로워 목록을 조회했습니다.",
            message_en="Successfully retrieved followers list.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=error_info.http_status,
            message_ko="팔로워 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving followers list.",
        )


@router.get("/stats/{user_id}", response_model=BaseResponse[FollowStatsResponse])
async def get_follow_stats(
    user_id: int = Path(..., description="사용자 ID"),
    current_user_id: Optional[int] = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """팔로우 통계 조회"""
    try:
        follow_service = FollowService(db)
        stats = await follow_service.get_follow_stats(
            user_id=user_id, current_user_id=current_user_id
        )

        return BaseResponse.ok(
            data=stats,
            http_status=HttpStatus.OK,
            message_ko="팔로우 통계를 조회했습니다.",
            message_en="Successfully retrieved follow statistics.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=error_info.http_status,
            message_ko="팔로우 통계 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving follow statistics.",
        )


@router.get("/pods", response_model=BaseResponse[PageDto[PodDto]])
async def get_following_users_pods(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """팔로우하는 사용자들이 만든 파티 목록 조회"""
    try:
        follow_service = FollowService(db)
        pods = await follow_service.get_following_pods(
            user_id=current_user_id, page=page, size=size
        )

        return BaseResponse.ok(
            data=pods,
            http_status=HttpStatus.OK,
            message_ko="팔로우하는 사용자의 파티 목록을 조회했습니다.",
            message_en="Successfully retrieved following users' pods.",
        )
    except Exception as e:
        import traceback

        print(f"팔로우하는 사용자의 파티 목록 조회 오류: {e}")
        traceback.print_exc()
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="팔로우하는 사용자의 파티 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving following users' pods.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.get("/recommend", response_model=BaseResponse[PageDto[SimpleUserDto]])
async def get_recommended_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """추천 유저 목록 조회"""
    try:
        follow_service = FollowService(db)
        users = await follow_service.get_recommended_users(
            user_id=current_user_id, page=page, size=size
        )

        return BaseResponse.ok(
            data=users,
            http_status=HttpStatus.OK,
            message_ko="추천 유저 목록을 조회했습니다.",
            message_en="Successfully retrieved recommended users.",
        )
    except Exception as e:
        import traceback

        print(f"추천 유저 목록 조회 오류: {e}")
        traceback.print_exc()
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse(
            data=None,
            http_status=error_info.http_status,
            message_ko="추천 유저 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving recommended users.",
            error=error_info.error_key,
            error_code=error_info.code,
            dev_note=None,
        )


@router.get(
    "/notification/{following_id}",
    response_model=BaseResponse[FollowNotificationStatusResponse],
)
async def get_notification_status(
    following_id: int = Path(..., description="팔로우한 사용자 ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """특정 팔로우한 유저의 알림 설정 상태 조회"""
    try:
        follow_service = FollowService(db)
        notification_status = await follow_service.get_notification_status(
            follower_id=current_user_id, following_id=following_id
        )

        if not notification_status:
            return BaseResponse(
                data=None,
                http_status=404,
                message_ko="팔로우 관계를 찾을 수 없습니다.",
                message_en="Follow relationship not found.",
                error="FOLLOW_NOT_FOUND",
                error_code=4001,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=notification_status,
            http_status=HttpStatus.OK,
            message_ko="알림 설정 상태를 조회했습니다.",
            message_en="Successfully retrieved notification status.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=error_info.http_status,
            message_ko="알림 설정 상태 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving notification status.",
        )


@router.put(
    "/notification", response_model=BaseResponse[FollowNotificationStatusResponse]
)
async def update_notification_status(
    request: FollowNotificationUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """특정 팔로우한 유저의 알림 설정 변경"""
    try:
        follow_service = FollowService(db)
        notification_status = await follow_service.update_notification_status(
            follower_id=current_user_id,
            following_id=request.following_id,
            notification_enabled=request.notification_enabled,
        )

        if not notification_status:
            return BaseResponse(
                data=None,
                http_status=404,
                message_ko="팔로우 관계를 찾을 수 없습니다.",
                message_en="Follow relationship not found.",
                error="FOLLOW_NOT_FOUND",
                error_code=4001,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=notification_status,
            http_status=HttpStatus.OK,
            message_ko="알림 설정이 변경되었습니다.",
            message_en="Successfully updated notification status.",
        )
    except Exception as e:
        error_info = get_error_info("INTERNAL_SERVER_ERROR")
        return BaseResponse.error(
            error_key=error_info.error_key,
            error_code=error_info.code,
            http_status=error_info.http_status,
            message_ko="알림 설정 변경 중 오류가 발생했습니다.",
            message_en="An error occurred while updating notification status.",
        )
