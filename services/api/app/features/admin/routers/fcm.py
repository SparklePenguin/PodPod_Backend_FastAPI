from enum import Enum

from app.common.schemas import BaseResponse
from app.core.database import get_session
from app.core.services.fcm_service import FCMService
from app.deps.auth import get_current_user_id
from app.features.users.repositories import UserRepository
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# 알림 타입 Enum
class NotificationType(str, Enum):
    """FCM 알림 타입"""

    # 파티 알림
    POD_JOIN_REQUEST = "POD_JOIN_REQUEST"
    POD_REQUEST_APPROVED = "POD_REQUEST_APPROVED"
    POD_REQUEST_REJECTED = "POD_REQUEST_REJECTED"
    POD_NEW_MEMBER = "POD_NEW_MEMBER"
    POD_UPDATED = "POD_UPDATED"
    POD_CONFIRMED = "POD_CONFIRMED"
    POD_CANCELED = "POD_CANCELED"
    POD_START_SOON = "POD_START_SOON"
    POD_LOW_ATTENDANCE = "POD_LOW_ATTENDANCE"

    # 파티 상태 알림
    POD_LIKES_THRESHOLD = "POD_LIKES_THRESHOLD"
    POD_VIEWS_THRESHOLD = "POD_VIEWS_THRESHOLD"

    # 추천 알림
    SAVED_POD_DEADLINE = "SAVED_POD_DEADLINE"
    SAVED_POD_SPOT_OPENED = "SAVED_POD_SPOT_OPENED"

    # 리뷰 알림
    REVIEW_CREATED = "REVIEW_CREATED"
    REVIEW_REMINDER_DAY = "REVIEW_REMINDER_DAY"
    REVIEW_REMINDER_WEEK = "REVIEW_REMINDER_WEEK"
    REVIEW_OTHERS_CREATED = "REVIEW_OTHERS_CREATED"

    # 팔로우 알림
    FOLLOWED_BY_USER = "FOLLOWED_BY_USER"
    FOLLOWED_USER_CREATED_POD = "FOLLOWED_USER_CREATED_POD"


class SendNotificationRequest(BaseModel):
    """알림 전송 요청"""

    user_id: int = Field(alias="userId", description="알림을 받을 사용자 ID")
    title: str = Field(description="알림 제목")
    body: str = Field(description="알림 내용")
    data: dict | None = Field(default=None, description="추가 데이터")

    model_config = {"populate_by_name": True}


# - MARK: FCM 테스트 알림 전송
@router.post(
    "/fcm/test",
    response_model=BaseResponse[dict],
    description="FCM 테스트 알림 전송",
)
async def send_test_notification(
    request: SendNotificationRequest, db: AsyncSession = Depends(get_session)
):
    """테스트용 FCM 알림 전송"""
    try:
        # FCM 서비스 초기화
        fcm_service = FCMService()

        # 사용자의 FCM 토큰 조회
        user_crud = UserRepository(db)
        user = await user_crud.get_by_id(request.user_id)

        if not user:
            return BaseResponse.error(
                error_key="USER_NOT_FOUND",
                error_code=4004,
                http_status=status.HTTP_404_NOT_FOUND,
                message_ko="사용자를 찾을 수 없습니다.",
                message_en="User not found.",
            )

        fcm_token: str | None = getattr(user, "fcm_token", None)
        if not fcm_token:
            return BaseResponse.error(
                error_key="FCM_TOKEN_NOT_FOUND",
                error_code=4005,
                http_status=status.HTTP_400_BAD_REQUEST,
                message_ko="사용자의 FCM 토큰이 없습니다. 로그인 시 fcmToken을 전송해주세요.",
                message_en="User's FCM token not found.",
            )

        # 알림 전송
        success = await fcm_service.send_notification(
            token=fcm_token, title=request.title, body=request.body, data=request.data
        )

        if success:
            return BaseResponse.ok(
                data={
                    "sent": True,
                    "userId": request.user_id,
                    "nickname": user.nickname,
                },
                message_ko="알림이 전송되었습니다.",
                message_en="Notification sent successfully.",
            )
        else:
            return BaseResponse.error(
                error_key="FCM_SEND_FAILED",
                error_code=5002,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message_ko="알림 전송에 실패했습니다.",
                message_en="Failed to send notification.",
            )

    except ValueError as e:
        # Firebase 설정 오류
        return BaseResponse.error(
            error_key="FIREBASE_CONFIG_ERROR",
            error_code=5003,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=str(e),
            message_en="Firebase configuration error.",
        )
    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5001,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=f"알림 전송 중 오류가 발생했습니다: {str(e)}",
            message_en="An error occurred while sending notification.",
        )


# - MARK: 내게 FCM 테스트 알림 전송
@router.post(
    "/fcm/test-self",
    response_model=BaseResponse[dict],
    description="내게 FCM 테스트 알림 전송",
)
async def send_test_notification_to_self(
    title: str = Query(default="테스트 알림", description="알림 제목"),
    body: str = Query(
        default="FCM 알림 테스트입니다.",
        description="알림 내용",
    ),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    """자신에게 테스트 알림 전송 (간편 테스트용)"""
    try:
        # FCM 서비스 초기화
        fcm_service = FCMService()

        # 현재 사용자의 FCM 토큰 조회
        user_crud = UserRepository(db)
        user = await user_crud.get_by_id(current_user_id)

        if not user:
            return BaseResponse.error(
                error_key="USER_NOT_FOUND",
                error_code=4004,
                http_status=status.HTTP_404_NOT_FOUND,
                message_ko="사용자를 찾을 수 없습니다.",
                message_en="User not found.",
            )

        fcm_token: str | None = getattr(user, "fcm_token", None)
        if not fcm_token:
            return BaseResponse.error(
                error_key="FCM_TOKEN_NOT_FOUND",
                error_code=4005,
                http_status=status.HTTP_400_BAD_REQUEST,
                message_ko="FCM 토큰이 없습니다. 로그인 시 fcmToken을 전송해주세요.",
                message_en="FCM token not found.",
            )

        # 알림 전송
        success = await fcm_service.send_notification(
            token=fcm_token,
            title=title,
            body=body,
            data={"type": "test", "test": "true"},
        )

        if success:
            return BaseResponse.ok(
                data={
                    "sent": True,
                    "userId": current_user_id,
                    "nickname": user.nickname,
                },
                message_ko="알림이 전송되었습니다.",
                message_en="Notification sent successfully.",
            )
        else:
            return BaseResponse.error(
                error_key="FCM_SEND_FAILED",
                error_code=5002,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message_ko="알림 전송에 실패했습니다.",
                message_en="Failed to send notification.",
            )

    except ValueError as e:
        return BaseResponse.error(
            error_key="FIREBASE_CONFIG_ERROR",
            error_code=5003,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=str(e),
            message_en="Firebase configuration error.",
        )
    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5001,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=f"알림 전송 중 오류가 발생했습니다: {str(e)}",
            message_en="An error occurred while sending notification.",
        )


# - MARK: 특정 타입의 FCM 알림 테스트
@router.post(
    "/fcm/test-notification-type",
    response_model=BaseResponse[dict],
    description="FCM 알림 전송",
)
async def send_notification_by_type(
    user_id: int = Query(..., alias="userId", description="알림을 받을 사용자 ID"),
    notification_type: NotificationType = Query(
        ..., alias="notificationType", description="알림 타입"
    ),
    party_name: str | None = Query(
        default="왕코가나지",
        alias="partyName",
        description="파티 이름 (선택)",
    ),
    nickname: str | None = Query(
        default="테스트유저",
        description="닉네임 (선택)",
    ),
    pod_id: int | None = Query(default=20, alias="podId", description="파티 ID (선택)"),
    review_id: int | None = Query(
        default=1, alias="reviewId", description="리뷰 ID (선택)"
    ),
    db: AsyncSession = Depends(get_session),
):
    """특정 알림 타입으로 테스트 알림 전송"""
    try:
        # FCM 서비스 초기화
        fcm_service = FCMService()

        # 사용자 FCM 토큰 조회
        user_crud = UserRepository(db)
        user = await user_crud.get_by_id(user_id)

        if not user:
            return BaseResponse.error(
                error_key="USER_NOT_FOUND",
                error_code=4004,
                http_status=status.HTTP_404_NOT_FOUND,
                message_ko="사용자를 찾을 수 없습니다.",
                message_en="User not found.",
            )

        fcm_token: str | None = getattr(user, "fcm_token", None)
        if not fcm_token:
            return BaseResponse.error(
                error_key="FCM_TOKEN_NOT_FOUND",
                error_code=4005,
                http_status=status.HTTP_400_BAD_REQUEST,
                message_ko="사용자의 FCM 토큰이 없습니다.",
                message_en="User's FCM token not found.",
            )

        # 기본값 설정 (타입 안전성을 위해)
        safe_party_name: str = party_name or "왕코가나지"
        safe_nickname: str = nickname or "테스트유저"
        safe_pod_id: int = pod_id or 20
        safe_review_id: int = review_id or 1

        # 알림 타입별로 적절한 함수 호출
        success = False
        if notification_type == NotificationType.POD_JOIN_REQUEST:
            success = await fcm_service.send_pod_join_request(
                token=fcm_token,
                nickname=safe_nickname,
                pod_id=safe_pod_id,
                db=db,
                user_id=user_id,
                related_user_id=10,  # 테스트용 신청자 ID
            )
        elif notification_type == NotificationType.POD_REQUEST_APPROVED:
            success = await fcm_service.send_pod_request_approved(
                token=fcm_token,
                party_name=safe_party_name,
                pod_id=safe_pod_id,
                db=db,
                user_id=user_id,
                related_user_id=6,  # 테스트용 승인자 ID
                related_pod_id=safe_pod_id,
            )
        elif notification_type == NotificationType.POD_REQUEST_REJECTED:
            success = await fcm_service.send_pod_request_rejected(
                token=fcm_token,
                party_name=safe_party_name,
                pod_id=safe_pod_id,
                db=db,
                user_id=user_id,
                related_user_id=6,  # 테스트용 거절자 ID
                related_pod_id=safe_pod_id,
            )
        elif notification_type == NotificationType.POD_NEW_MEMBER:
            success = await fcm_service.send_pod_new_member(
                fcm_token, safe_nickname, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.POD_UPDATED:
            success = await fcm_service.send_pod_updated(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.POD_CONFIRMED:
            success = await fcm_service.send_pod_confirmed(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.POD_CANCELED:
            success = await fcm_service.send_pod_canceled(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.POD_START_SOON:
            success = await fcm_service.send_pod_start_soon(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.POD_LOW_ATTENDANCE:
            success = await fcm_service.send_pod_low_attendance(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.POD_LIKES_THRESHOLD:
            success = await fcm_service.send_pod_likes_threshold(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.POD_VIEWS_THRESHOLD:
            success = await fcm_service.send_pod_views_threshold(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.SAVED_POD_DEADLINE:
            success = await fcm_service.send_saved_pod_deadline(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.SAVED_POD_SPOT_OPENED:
            success = await fcm_service.send_saved_pod_spot_opened(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.REVIEW_CREATED:
            success = await fcm_service.send_review_created(
                fcm_token, safe_nickname, safe_party_name, safe_review_id
            )
        elif notification_type == NotificationType.REVIEW_REMINDER_DAY:
            success = await fcm_service.send_review_reminder_day(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.REVIEW_REMINDER_WEEK:
            success = await fcm_service.send_review_reminder_week(
                fcm_token, safe_party_name, safe_pod_id
            )
        elif notification_type == NotificationType.REVIEW_OTHERS_CREATED:
            success = await fcm_service.send_review_others_created(
                fcm_token, safe_nickname, safe_review_id, safe_pod_id
            )
        elif notification_type == NotificationType.FOLLOWED_BY_USER:
            success = await fcm_service.send_followed_by_user(
                fcm_token, safe_nickname, user_id
            )
        elif notification_type == NotificationType.FOLLOWED_USER_CREATED_POD:
            success = await fcm_service.send_followed_user_created_pod(
                fcm_token, safe_nickname, safe_party_name, safe_pod_id
            )

        if success:
            return BaseResponse.ok(
                data={
                    "sent": True,
                    "userId": user_id,
                    "nickname": user.nickname,
                    "notificationType": notification_type.value,
                },
                message_ko="알림이 전송되었습니다.",
                message_en="Notification sent successfully.",
            )
        else:
            return BaseResponse.error(
                error_key="FCM_SEND_FAILED",
                error_code=5002,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message_ko="알림 전송에 실패했습니다.",
                message_en="Failed to send notification.",
            )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5001,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=f"알림 전송 중 오류가 발생했습니다: {str(e)}",
            message_en="An error occurred while sending notification.",
        )
