"""
Firebase Cloud Messaging 인프라 모듈

순수 FCM 전송 기능만 포함합니다.
비즈니스 로직(알림 설정 확인, DB 저장 등)은 각 feature의 서비스에서 처리합니다.
"""

import json
import logging

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

logger = logging.getLogger(__name__)


class FCMClient:
    """Firebase Cloud Messaging 클라이언트 (순수 인프라)"""

    _initialized = False

    def __init__(self):
        """FCM 클라이언트 초기화"""
        if not FCMClient._initialized:
            try:
                if not hasattr(settings, "FIREBASE_SERVICE_ACCOUNT_KEY"):
                    raise ValueError(
                        "Firebase 서비스 계정 키가 설정되지 않았습니다. "
                        "FIREBASE_SERVICE_ACCOUNT_KEY 환경변수를 설정해주세요."
                    )

                firebase_key = settings.FIREBASE_SERVICE_ACCOUNT_KEY
                if not firebase_key:
                    raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY 환경변수가 비어있습니다.")

                service_account_info = json.loads(firebase_key)
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)

                FCMClient._initialized = True
                logger.info("Firebase Admin SDK 초기화 완료")

            except ValueError as e:
                logger.warning(f"Firebase 설정 오류: {e}")
                raise
            except Exception as e:
                logger.error(f"Firebase 초기화 실패: {e}")
                raise

    def send_message(
        self,
        token: str,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> tuple[bool, str | None]:
        """
        FCM 푸시 알림 전송

        Args:
            token: FCM 토큰
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터 (선택사항)

        Returns:
            (성공 여부, 에러 메시지 또는 None)
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
            )

            response = messaging.send(message)
            logger.info(f"FCM 알림 전송 성공: {response}")
            return True, None

        except Exception as e:
            error_message = str(e)
            logger.error(f"FCM 알림 전송 실패: {error_message}")
            return False, error_message

    def send_multicast_message(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict | None = None,
    ) -> dict:
        """
        여러 사용자에게 FCM 푸시 알림 전송

        Args:
            tokens: FCM 토큰 리스트
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터 (선택사항)

        Returns:
            {"success_count": int, "failure_count": int, "responses": list}
        """
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                tokens=tokens,
            )

            response: messaging.BatchResponse = messaging.send_multicast(message)

            logger.info(
                f"FCM 멀티캐스트 알림 전송 완료: "
                f"성공 {response.success_count}, 실패 {response.failure_count}"
            )

            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": response.responses,
            }

        except Exception as e:
            error_message = str(e)
            logger.error(f"FCM 멀티캐스트 알림 전송 실패: {error_message}")

            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "responses": [],
            }

    @staticmethod
    def is_token_invalid_error(error_message: str) -> bool:
        """토큰 무효화가 필요한 에러인지 확인"""
        return "InvalidRegistration" in error_message

    @staticmethod
    def is_apns_auth_error(error_message: str) -> bool:
        """APNS 인증 에러인지 확인 (토큰은 유효함)"""
        return "Auth error from APNS" in error_message


# 싱글톤 인스턴스 (lazy initialization)
_fcm_client: FCMClient | None = None


def get_fcm_client() -> FCMClient:
    """FCM 클라이언트 싱글톤 인스턴스 반환"""
    global _fcm_client
    if _fcm_client is None:
        _fcm_client = FCMClient()
    return _fcm_client
