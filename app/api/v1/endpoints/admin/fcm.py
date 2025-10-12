from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from app.api.deps import get_current_user_id
from app.schemas.common import BaseResponse
from app.core.http_status import HttpStatus
from app.services.fcm_service import FCMService
from app.crud.user import UserCRUD
from app.core.database import get_db
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
    title: str = Field(alias="title", description="알림 제목")
    body: str = Field(alias="body", description="알림 내용")
    data: Optional[dict] = Field(default=None, alias="data", description="추가 데이터")

    model_config = {"populate_by_name": True}


@router.post(
    "/fcm/test",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "알림 전송 성공",
        },
    },
    summary="FCM 테스트 알림 전송",
    description="⚠️ 테스트용 - 특정 사용자에게 FCM 푸시 알림을 전송합니다. (인증 불필요)",
    tags=["admin"],
)
async def send_test_notification(
    request: SendNotificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """테스트용 FCM 알림 전송"""
    try:
        # FCM 서비스 초기화
        fcm_service = FCMService()

        # 사용자의 FCM 토큰 조회
        user_crud = UserCRUD(db)
        user = await user_crud.get_by_id(request.user_id)

        if not user:
            return BaseResponse.error(
                error_key="USER_NOT_FOUND",
                error_code=4004,
                http_status=HttpStatus.NOT_FOUND,
                message_ko="사용자를 찾을 수 없습니다.",
                message_en="User not found.",
            )

        if not user.fcm_token:
            return BaseResponse.error(
                error_key="FCM_TOKEN_NOT_FOUND",
                error_code=4005,
                http_status=HttpStatus.BAD_REQUEST,
                message_ko="사용자의 FCM 토큰이 없습니다. 로그인 시 fcmToken을 전송해주세요.",
                message_en="User's FCM token not found.",
            )

        # 알림 전송
        success = await fcm_service.send_notification(
            token=user.fcm_token,
            title=request.title,
            body=request.body,
            data=request.data,
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
                http_status=HttpStatus.INTERNAL_SERVER_ERROR,
                message_ko="알림 전송에 실패했습니다.",
                message_en="Failed to send notification.",
            )

    except ValueError as e:
        # Firebase 설정 오류
        return BaseResponse.error(
            error_key="FIREBASE_CONFIG_ERROR",
            error_code=5003,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=str(e),
            message_en="Firebase configuration error.",
        )
    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5001,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=f"알림 전송 중 오류가 발생했습니다: {str(e)}",
            message_en="An error occurred while sending notification.",
        )


@router.post(
    "/fcm/test-self",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "알림 전송 성공",
        },
    },
    summary="내게 FCM 테스트 알림 전송",
    description="⚠️ 테스트용 - 자신에게 FCM 푸시 알림을 전송합니다.",
    tags=["admin"],
)
async def send_test_notification_to_self(
    title: str = Query(default="테스트 알림", alias="title", description="알림 제목"),
    body: str = Query(
        default="FCM 알림 테스트입니다.", alias="body", description="알림 내용"
    ),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """자신에게 테스트 알림 전송 (간편 테스트용)"""
    try:
        # FCM 서비스 초기화
        fcm_service = FCMService()

        # 현재 사용자의 FCM 토큰 조회
        user_crud = UserCRUD(db)
        user = await user_crud.get_by_id(current_user_id)

        if not user.fcm_token:
            return BaseResponse.error(
                error_key="FCM_TOKEN_NOT_FOUND",
                error_code=4005,
                http_status=HttpStatus.BAD_REQUEST,
                message_ko="FCM 토큰이 없습니다. 로그인 시 fcmToken을 전송해주세요.",
                message_en="FCM token not found.",
            )

        # 알림 전송
        success = await fcm_service.send_notification(
            token=user.fcm_token,
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
                http_status=HttpStatus.INTERNAL_SERVER_ERROR,
                message_ko="알림 전송에 실패했습니다.",
                message_en="Failed to send notification.",
            )

    except ValueError as e:
        return BaseResponse.error(
            error_key="FIREBASE_CONFIG_ERROR",
            error_code=5003,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=str(e),
            message_en="Firebase configuration error.",
        )
    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5001,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=f"알림 전송 중 오류가 발생했습니다: {str(e)}",
            message_en="An error occurred while sending notification.",
        )


@router.post(
    "/fcm/test-notification-type",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "알림 전송 성공",
        },
    },
    summary="특정 타입의 FCM 알림 테스트",
    description="⚠️ 테스트용 - 특정 알림 타입으로 FCM 푸시 알림을 전송합니다. (인증 불필요)",
    tags=["admin"],
)
async def send_notification_by_type(
    user_id: int = Query(..., alias="userId", description="알림을 받을 사용자 ID"),
    notification_type: NotificationType = Query(
        ..., alias="notificationType", description="알림 타입"
    ),
    party_name: Optional[str] = Query(
        default="왕코가나지", alias="partyName", description="파티 이름 (선택)"
    ),
    nickname: Optional[str] = Query(
        default="테스트유저", alias="nickname", description="닉네임 (선택)"
    ),
    pod_id: Optional[int] = Query(
        default=20, alias="podId", description="파티 ID (선택)"
    ),
    review_id: Optional[int] = Query(
        default=1, alias="reviewId", description="리뷰 ID (선택)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """특정 알림 타입으로 테스트 알림 전송"""
    try:
        # FCM 서비스 초기화
        fcm_service = FCMService(db)

        # 사용자 FCM 토큰 조회
        user_crud = UserCRUD(db)
        user = await user_crud.get_by_id(user_id)

        if not user:
            return BaseResponse.error(
                error_key="USER_NOT_FOUND",
                error_code=4004,
                http_status=HttpStatus.NOT_FOUND,
                message_ko="사용자를 찾을 수 없습니다.",
                message_en="User not found.",
            )

        if not user.fcm_token:
            return BaseResponse.error(
                error_key="FCM_TOKEN_NOT_FOUND",
                error_code=4005,
                http_status=HttpStatus.BAD_REQUEST,
                message_ko="사용자의 FCM 토큰이 없습니다.",
                message_en="User's FCM token not found.",
            )

        # 알림 타입별로 적절한 함수 호출
        success = False
        if notification_type == NotificationType.POD_JOIN_REQUEST:
            success = await fcm_service.send_pod_join_request(
                token=user.fcm_token,
                nickname=nickname,
                pod_id=pod_id,
                db=db,
                user_id=user_id,
                related_user_id=10,  # 테스트용 신청자 ID
                related_pod_id=pod_id,
            )
        elif notification_type == NotificationType.POD_REQUEST_APPROVED:
            success = await fcm_service.send_pod_request_approved(
                token=user.fcm_token,
                party_name=party_name,
                pod_id=pod_id,
                db=db,
                user_id=user_id,
                related_user_id=6,  # 테스트용 승인자 ID
                related_pod_id=pod_id,
            )
        elif notification_type == NotificationType.POD_REQUEST_REJECTED:
            success = await fcm_service.send_pod_request_rejected(
                token=user.fcm_token,
                party_name=party_name,
                pod_id=pod_id,
                db=db,
                user_id=user_id,
                related_user_id=6,  # 테스트용 거절자 ID
                related_pod_id=pod_id,
            )
        elif notification_type == NotificationType.POD_NEW_MEMBER:
            success = await fcm_service.send_pod_new_member(
                user.fcm_token, nickname, party_name, pod_id
            )
        elif notification_type == NotificationType.POD_UPDATED:
            success = await fcm_service.send_pod_updated(
                user.fcm_token, party_name, pod_id
            )
        elif notification_type == NotificationType.POD_CONFIRMED:
            success = await fcm_service.send_pod_confirmed(
                user.fcm_token, party_name, pod_id
            )
        elif notification_type == NotificationType.POD_CANCELED:
            success = await fcm_service.send_pod_canceled(
                user.fcm_token, party_name, pod_id
            )
        elif notification_type == NotificationType.POD_START_SOON:
            success = await fcm_service.send_pod_start_soon(
                user.fcm_token, party_name, pod_id
            )
        elif notification_type == NotificationType.POD_LOW_ATTENDANCE:
            success = await fcm_service.send_pod_low_attendance(
                user.fcm_token, party_name, pod_id
            )
        elif notification_type == NotificationType.POD_LIKES_THRESHOLD:
            success = await fcm_service.send_pod_likes_threshold(
                user.fcm_token, party_name
            )
        elif notification_type == NotificationType.POD_VIEWS_THRESHOLD:
            success = await fcm_service.send_pod_views_threshold(
                user.fcm_token, party_name
            )
        elif notification_type == NotificationType.SAVED_POD_DEADLINE:
            success = await fcm_service.send_saved_pod_deadline(
                user.fcm_token, party_name, pod_id
            )
        elif notification_type == NotificationType.SAVED_POD_SPOT_OPENED:
            success = await fcm_service.send_saved_pod_spot_opened(
                user.fcm_token, party_name, pod_id
            )
        elif notification_type == NotificationType.REVIEW_CREATED:
            success = await fcm_service.send_review_created(
                user.fcm_token, nickname, party_name, review_id
            )
        elif notification_type == NotificationType.REVIEW_REMINDER_DAY:
            success = await fcm_service.send_review_reminder_day(
                user.fcm_token, party_name
            )
        elif notification_type == NotificationType.REVIEW_REMINDER_WEEK:
            success = await fcm_service.send_review_reminder_week(
                user.fcm_token, party_name
            )
        elif notification_type == NotificationType.REVIEW_OTHERS_CREATED:
            success = await fcm_service.send_review_others_created(
                user.fcm_token, nickname, review_id
            )
        elif notification_type == NotificationType.FOLLOWED_BY_USER:
            success = await fcm_service.send_followed_by_user(
                user.fcm_token, nickname, user_id
            )
        elif notification_type == NotificationType.FOLLOWED_USER_CREATED_POD:
            success = await fcm_service.send_followed_user_created_pod(
                user.fcm_token, nickname, party_name, pod_id
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
                http_status=HttpStatus.INTERNAL_SERVER_ERROR,
                message_ko="알림 전송에 실패했습니다.",
                message_en="Failed to send notification.",
            )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5001,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=f"알림 전송 중 오류가 발생했습니다: {str(e)}",
            message_en="An error occurred while sending notification.",
        )
