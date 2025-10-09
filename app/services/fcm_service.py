import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional, List
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class FCMService:
    """Firebase Cloud Messaging 서비스"""

    _initialized = False

    def __init__(self):
        """FCM 서비스 초기화"""
        if not FCMService._initialized:
            try:
                # Firebase 서비스 계정 키 확인
                if not hasattr(settings, "FIREBASE_SERVICE_ACCOUNT_KEY"):
                    raise ValueError(
                        "Firebase 서비스 계정 키가 설정되지 않았습니다. "
                        "FIREBASE_SERVICE_ACCOUNT_KEY 환경변수를 설정해주세요."
                    )

                # JSON 문자열을 dict로 변환
                import json

                service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_KEY)

                # Firebase Admin SDK 초기화
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)

                FCMService._initialized = True
                logger.info("Firebase Admin SDK 초기화 완료")

            except ValueError as e:
                logger.warning(f"Firebase 설정 오류: {e}")
                raise
            except Exception as e:
                logger.error(f"Firebase 초기화 실패: {e}")
                raise

    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> bool:
        """
        FCM 푸시 알림 전송

        Args:
            token: FCM 토큰
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터 (선택사항)

        Returns:
            성공 여부
        """
        try:
            # 메시지 생성
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
            )

            # 메시지 전송
            response = messaging.send(message)
            logger.info(f"FCM 알림 전송 성공: {response}")
            return True

        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: {e}")
            return False

    async def send_multicast_notification(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> dict:
        """
        여러 사용자에게 FCM 푸시 알림 전송

        Args:
            tokens: FCM 토큰 리스트
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터 (선택사항)

        Returns:
            {"success_count": int, "failure_count": int}
        """
        try:
            # 멀티캐스트 메시지 생성
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=tokens,
            )

            # 메시지 전송
            response = messaging.send_multicast(message)

            logger.info(
                f"FCM 멀티캐스트 알림 전송 완료: "
                f"성공 {response.success_count}, 실패 {response.failure_count}"
            )

            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
            }

        except Exception as e:
            logger.error(f"FCM 멀티캐스트 알림 전송 실패: {e}")
            return {
                "success_count": 0,
                "failure_count": len(tokens),
            }
