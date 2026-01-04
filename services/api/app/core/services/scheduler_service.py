import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from app.core.database import get_session
from app.core.services.fcm_service import FCMService
from app.features.pods.models import (
    Pod,
    PodLike,
    PodMember,
    PodRating,
    PodStatus,
)
from app.features.users.models import User
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SchedulerService:
    """스케줄러 서비스 - 주기적인 작업 처리"""

    def __init__(self):
        self.fcm_service = FCMService()

    async def check_review_reminders(self):
        """모임 종료 후 리뷰 유도 알림 체크 (1시간마다)"""
        try:
            # 데이터베이스 세션 생성
            async for db in get_session():
                try:
                    # 파티 상태 자동 변경 (미팅일이 된 확정 파티를 종료로)
                    await self._update_completed_pods_to_closed(db)

                    # 1일 전 모임들 조회 (REVIEW_REMINDER_DAY)
                    await self._send_day_reminders(db)

                    # 1주일 전 모임들 조회 (REVIEW_REMINDER_WEEK)
                    await self._send_week_reminders(db)

                    # 파티 마감 임박 알림 (모집 중이고 내일 마감되는 파티)
                    await self._send_low_attendance_reminders(db)

                    # 좋아요한 파티 마감 임박 알림 (1일 전)
                    await self._send_saved_pod_deadline_reminders(db)

                finally:
                    await db.close()

        except Exception as e:
            logger.error(f"리뷰 리마인드 체크 중 오류: {e}")

    async def check_start_soon_reminders(self):
        """파티 시작 1시간 전 알림 체크 (5분마다)"""
        try:
            # 데이터베이스 세션 생성
            async for db in get_session():
                try:
                    # 파티 상태 자동 변경 (미팅일이 지난 확정 파티를 종료로)
                    await self._update_completed_pods_to_closed(db)

                    # 모집 중인데 확정 안된 파티를 취소로 변경
                    await self._cancel_unconfirmed_pods(db)

                    # 파티 시작 임박 알림 (1시간 전)
                    await self._send_start_soon_reminders(db)

                    # 파티 취소 임박 알림 (모집 중 상태 / 1시간 전)
                    await self._send_canceled_soon_reminders(db)

                finally:
                    await db.close()

        except Exception as e:
            logger.error(f"파티 시작 임박 알림 체크 중 오류: {e}")

    async def check_deadline_reminders(self):
        """마감 임박 알림 체크 (1시간마다)"""
        try:
            # 데이터베이스 세션 생성
            async for db in get_session():
                try:
                    # 파티 마감 임박 알림 (24시간 전 + 인원 부족)
                    await self._send_low_attendance_reminders(db)

                    # 좋아요한 파티 마감 임박 알림 (1일 전)
                    await self._send_saved_pod_deadline_reminders(db)

                finally:
                    await db.close()

        except Exception as e:
            logger.error(f"마감 임박 알림 체크 중 오류: {e}")

    async def _has_sent_review_reminder(
        self, db: AsyncSession, user_id: int, pod_id: int, reminder_type: str
    ) -> bool:
        """리뷰 리마인드 알림을 이미 보냈는지 확인"""
        from app.features.notifications.models import Notification

        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.related_pod_id == pod_id,
                Notification.notification_value == reminder_type,
                Notification.created_at >= date.today(),  # 오늘 보낸 것만 확인
            )
        )

        result = await db.execute(query)
        existing_notification = result.scalar_one_or_none()

        return existing_notification is not None

    async def _has_sent_start_soon_reminder(
        self, db: AsyncSession, user_id: int, pod_id: int
    ) -> bool:
        """파티 시작 임박 알림을 이미 보냈는지 확인"""
        from app.features.notifications.models import Notification

        # 디버깅: 해당 사용자의 모든 POD_START_SOON 알림 조회
        debug_query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.notification_value == "POD_START_SOON",
                Notification.created_at >= date.today(),
            )
        )
        debug_result = await db.execute(debug_query)
        debug_notifications = debug_result.scalars().all()

        logger.info(
            f"디버깅: user_id={user_id}의 오늘 POD_START_SOON 알림 {len(debug_notifications)}개"
        )
        for notif in debug_notifications:
            logger.info(
                f"  - 알림 ID: {notif.id}, related_pod_id: {notif.related_pod_id}, related_id: {notif.related_id}"
            )

        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.notification_value == "POD_START_SOON",
                Notification.created_at >= date.today(),  # 오늘 보낸 것만 확인
                # related_pod_id 또는 related_id 중 하나라도 일치하면 중복
                or_(
                    Notification.related_pod_id == pod_id,
                    Notification.related_id == str(pod_id),
                ),
            )
        )

        result = await db.execute(query)
        existing_notifications = result.scalars().all()

        logger.info(
            f"중복 체크: user_id={user_id}, pod_id={pod_id}, 기존 알림 존재={len(existing_notifications) > 0}"
        )
        return len(existing_notifications) > 0

    async def _send_day_reminders(self, db: AsyncSession):
        """1일 전 모임 리뷰 유도 알림"""
        yesterday = date.today() - timedelta(days=1)

        # 어제 종료된 모임들 조회
        # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
        query = select(Pod).where(
            and_(
                Pod.meeting_date == yesterday,
                func.upper(Pod.status)
                == PodStatus.COMPLETED.value.upper(),  # 대소문자 무시 비교
            )
        )

        result = await db.execute(query)
        completed_pods = result.scalars().all()

        for pod in completed_pods:
            # 모임 참여자들에게 리뷰 유도 알림 전송
            await self._send_review_reminder_to_participants(
                db, pod, "REVIEW_REMINDER_DAY"
            )

    async def _send_week_reminders(self, db: AsyncSession):
        """1주일 전 모임 리뷰 리마인드 알림 (리뷰 미작성자만)"""
        week_ago = date.today() - timedelta(days=7)

        # 1주일 전 종료된 모임들 조회
        # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
        query = select(Pod).where(
            and_(
                Pod.meeting_date == week_ago,
                func.upper(Pod.status)
                == PodStatus.COMPLETED.value.upper(),  # 대소문자 무시 비교
            )
        )

        result = await db.execute(query)
        completed_pods = result.scalars().all()

        for pod in completed_pods:
            # 리뷰 미작성자들에게만 리마인드 알림 전송
            await self._send_review_reminder_to_non_reviewers(
                db, pod, "REVIEW_REMINDER_WEEK"
            )

    async def _send_review_reminder_to_participants(
        self, db: AsyncSession, pod: Pod, reminder_type: str
    ):
        """모임 참여자들에게 리뷰 유도 알림 전송"""
        try:
            # 모임 참여자 목록 조회
            participants_query = (
                select(User)
                .join(PodMember, User.id == PodMember.user_id)
                .where(PodMember.pod_id == pod.id)
                .distinct()
            )

            # 파티장도 포함
            owner_query = select(User).where(User.id == pod.owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            result = await db.execute(participants_query)
            participants = list(result.scalars().all())

            if owner and owner not in participants:
                participants.append(owner)

            # 각 참여자에게 알림 전송
            for participant in participants:
                try:
                    participant_id = getattr(participant, "id", None)
                    pod_id = getattr(pod, "id", None)
                    if participant_id is None or pod_id is None:
                        continue

                    # 이미 오늘 같은 알림을 보냈는지 확인
                    if await self._has_sent_review_reminder(
                        db, participant_id, pod_id, reminder_type
                    ):
                        logger.info(
                            f"{reminder_type} 알림 이미 전송됨: user_id={participant_id}, pod_id={pod_id}"
                        )
                        continue

                    fcm_token = getattr(participant, "fcm_token", None)
                    if fcm_token:
                        pod_title = getattr(pod, "title", "") or ""
                        if reminder_type == "REVIEW_REMINDER_DAY":
                            await self.fcm_service.send_review_reminder_day(
                                token=fcm_token,
                                party_name=pod_title,
                                pod_id=pod_id,
                                db=db,
                                user_id=participant_id,
                            )
                        elif reminder_type == "REVIEW_REMINDER_WEEK":
                            await self.fcm_service.send_review_reminder_week(
                                token=fcm_token,
                                party_name=pod_title,
                                pod_id=pod_id,
                                db=db,
                                user_id=participant_id,
                            )

                        logger.info(
                            f"{reminder_type} 알림 전송 성공: user_id={participant_id}, pod_id={pod_id}"
                        )
                    else:
                        logger.warning(
                            f"FCM 토큰이 없는 사용자: user_id={participant_id}"
                        )

                except Exception as e:
                    logger.error(
                        f"{reminder_type} 알림 전송 실패: user_id={participant.id}, error={e}"
                    )

        except Exception as e:
            logger.error(f"참여자 리뷰 리마인드 처리 실패: pod_id={pod.id}, error={e}")

    async def _send_review_reminder_to_non_reviewers(
        self, db: AsyncSession, pod: Pod, reminder_type: str
    ):
        """리뷰 미작성자들에게만 리마인드 알림 전송 (파티장 제외)"""
        try:
            # 모임 참여자 목록 조회
            participants_query = (
                select(User)
                .join(PodMember, User.id == PodMember.user_id)
                .where(PodMember.pod_id == pod.id)
                .distinct()
            )

            result = await db.execute(participants_query)
            participants = result.scalars().all()

            # 리뷰를 작성한 사용자들 조회
            reviewers_query = select(PodRating.user_id).where(
                PodRating.pod_id == pod.id
            )
            reviewers_result = await db.execute(reviewers_query)
            reviewer_ids = {row[0] for row in reviewers_result.all()}

            # 리뷰 미작성자들에게만 알림 전송 (파티장 제외)
            pod_owner_id = getattr(pod, "owner_id", None)
            pod_id = getattr(pod, "id", None)
            pod_title = getattr(pod, "title", "") or ""

            for participant in participants:
                participant_id = getattr(participant, "id", None)
                if participant_id is None or pod_owner_id is None:
                    continue

                # 파티장 제외
                if participant_id == pod_owner_id:
                    continue
                if participant_id not in reviewer_ids:
                    try:
                        if pod_id is None:
                            continue

                        # 이미 오늘 같은 알림을 보냈는지 확인
                        if await self._has_sent_review_reminder(
                            db, participant_id, pod_id, reminder_type
                        ):
                            logger.info(
                                f"{reminder_type} 알림 이미 전송됨: user_id={participant_id}, pod_id={pod_id}"
                            )
                            continue

                        fcm_token = getattr(participant, "fcm_token", None)
                        if fcm_token:
                            await self.fcm_service.send_review_reminder_week(
                                token=fcm_token,
                                party_name=pod_title,
                                pod_id=pod_id,
                                db=db,
                                user_id=participant_id,
                            )
                            logger.info(
                                f"리뷰 미작성자 리마인드 알림 전송 성공: user_id={participant_id}, pod_id={pod_id}"
                            )
                        else:
                            logger.warning(
                                f"FCM 토큰이 없는 사용자: user_id={participant.id}"
                            )

                    except Exception as e:
                        logger.error(
                            f"리뷰 미작성자 리마인드 알림 전송 실패: user_id={participant.id}, error={e}"
                        )

        except Exception as e:
            logger.error(
                f"리뷰 미작성자 리마인드 처리 실패: pod_id={pod.id}, error={e}"
            )

    async def _send_start_soon_reminders(self, db: AsyncSession):
        """파티 시작 1시간 전 알림"""
        now = datetime.now(timezone.utc)
        one_hour_later = now + timedelta(hours=1)

        logger.info(f"현재 시간: {now}")
        logger.info(f"1시간 후: {one_hour_later}")
        logger.info(f"오늘 날짜: {now.date()}")

        # 디버깅: 오늘 날짜의 모든 파티 조회
        debug_query = select(Pod).where(Pod.meeting_date == now.date())
        debug_result = await db.execute(debug_query)
        today_pods = debug_result.scalars().all()

        logger.info(f"오늘 날짜의 모든 파티: {len(today_pods)}개")
        for pod in today_pods:
            # status 접근 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
            try:
                status_str = str(pod.status).upper()
            except Exception:
                status_str = "UNKNOWN"
            logger.info(
                f"- 파티 ID: {pod.id}, 제목: {pod.title}, 시간: {pod.meeting_time}, 상태: {status_str}"
            )

        # 1시간 후 시작하는 모임들 조회
        # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
        query = select(Pod).where(
            and_(
                Pod.meeting_date == now.date(),
                Pod.meeting_time >= now.time(),
                Pod.meeting_time <= one_hour_later.time(),
                func.upper(Pod.status)
                == PodStatus.COMPLETED.value.upper(),  # 대소문자 무시 비교
            )
        )

        result = await db.execute(query)
        starting_soon_pods = result.scalars().all()

        logger.info(f"파티 시작 임박 알림 대상: {len(starting_soon_pods)}개")
        for pod in starting_soon_pods:
            # status 접근 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
            try:
                status_str = str(pod.status).upper()
            except Exception:
                status_str = "UNKNOWN"
            logger.info(
                f"- 파티 ID: {pod.id}, 제목: {pod.title}, 시간: {pod.meeting_time}, 상태: {status_str}"
            )

        for pod in starting_soon_pods:
            try:
                # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
                pod_status = str(pod.status).upper()
                if pod_status == PodStatus.COMPLETED.value:
                    await self._send_start_soon_to_participants(db, pod)
            except Exception as e:
                logger.error(
                    f"파티 시작 임박 알림 전송 실패: pod_id={pod.id}, error={e}"
                )

    async def _send_start_soon_to_participants(self, db: AsyncSession, pod: Pod):
        """파티 시작 임박 알림을 참여자들에게 전송"""
        try:
            # 모임 참여자 목록 조회
            participants_query = (
                select(User)
                .join(PodMember, User.id == PodMember.user_id)
                .where(PodMember.pod_id == pod.id)
                .distinct()
            )

            # 파티장도 포함
            owner_query = select(User).where(User.id == pod.owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            result = await db.execute(participants_query)
            participants = list(result.scalars().all())

            if owner and owner not in participants:
                participants.append(owner)

            # 각 참여자에게 알림 전송
            for participant in participants:
                try:
                    participant_id = getattr(participant, "id", None)
                    pod_id = getattr(pod, "id", None)
                    pod_owner_id = getattr(pod, "owner_id", None)
                    if participant_id is None or pod_id is None:
                        continue

                    # 이미 오늘 같은 알림을 보냈는지 확인
                    if await self._has_sent_start_soon_reminder(
                        db, participant_id, pod_id
                    ):
                        logger.info(
                            f"파티 시작 임박 알림 이미 전송됨: user_id={participant_id}, pod_id={pod_id}"
                        )
                        continue

                    fcm_token = getattr(participant, "fcm_token", None)
                    if fcm_token:
                        pod_title = getattr(pod, "title", "") or ""
                        await self.fcm_service.send_pod_start_soon(
                            token=fcm_token,
                            party_name=pod_title,
                            pod_id=pod_id,
                            db=db,
                            user_id=participant_id,
                            related_user_id=pod_owner_id,
                        )
                        logger.info(
                            f"파티 시작 임박 알림 전송 성공: user_id={participant_id}, pod_id={pod_id}"
                        )
                    else:
                        logger.warning(
                            f"FCM 토큰이 없는 사용자: user_id={participant_id}"
                        )

                except Exception as e:
                    participant_id = (
                        getattr(participant, "id", None) if participant else None
                    )
                    logger.error(
                        f"파티 시작 임박 알림 전송 실패: user_id={participant_id}, error={e}"
                    )

        except Exception as e:
            logger.error(f"파티 시작 임박 알림 처리 실패: pod_id={pod.id}, error={e}")

    async def _send_low_attendance_reminders(self, db: AsyncSession):
        """파티 마감 임박 알림 (모집 중이고 24시간 안에 마감되는 파티)"""
        now = datetime.now(timezone.utc)
        twenty_four_hours_later = now + timedelta(hours=24)
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # 24시간 안에 마감되는 모집 중인 파티들 조회
        # 조건: meeting_date + meeting_time이 now와 now + 24hours 사이
        # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)

        # 오늘 날짜이고 현재 시간 이후인 파티
        today_query = select(Pod).where(
            and_(
                Pod.meeting_date == today,
                Pod.meeting_time >= now.time(),
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper(),
            )
        )

        # 내일 날짜이고 24시간 이내인 파티
        tomorrow_query = select(Pod).where(
            and_(
                Pod.meeting_date == tomorrow,
                Pod.meeting_time <= twenty_four_hours_later.time(),
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper(),
            )
        )

        # 두 쿼리 결과 합치기
        today_result = await db.execute(today_query)
        tomorrow_result = await db.execute(tomorrow_query)
        today_pods = today_result.scalars().all()
        tomorrow_pods = tomorrow_result.scalars().all()

        # 모든 파티를 합치고, 실제로 24시간 안에 마감되는지 확인
        all_pods = list(today_pods) + list(tomorrow_pods)
        closing_soon_pods = []

        for pod in all_pods:
            # meeting_date + meeting_time을 datetime으로 결합 (UTC로 해석)
            meeting_date = getattr(pod, "meeting_date", None)
            meeting_time = getattr(pod, "meeting_time", None)
            if meeting_date is None or meeting_time is None:
                continue
            meeting_datetime = datetime.combine(
                meeting_date, meeting_time, tzinfo=timezone.utc
            )

            # 24시간 안에 마감되는지 확인
            if now <= meeting_datetime <= twenty_four_hours_later:
                closing_soon_pods.append(pod)

        logger.info(
            f"파티 마감 임박 알림 대상: {len(closing_soon_pods)}개 (24시간 안에 마감, 모집 중)"
        )

        for pod in closing_soon_pods:
            # 모집 중이고 24시간 안에 마감되는 파티면 알림 전송 (중복 체크는 _send_low_attendance_to_owner에서 처리)
            await self._send_low_attendance_to_owner(db, pod)

    async def _send_low_attendance_to_owner(self, db: AsyncSession, pod: Pod):
        """파티장에게 파티 마감 임박 알림 전송 (최근 24시간 내 이미 보낸 경우 제외)"""
        try:
            # 최근 24시간 내 같은 알림이 이미 있는지 확인
            from datetime import datetime, timedelta, timezone

            from app.features.notifications.models import Notification

            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

            existing_notification_query = select(Notification).where(
                and_(
                    Notification.user_id == pod.owner_id,
                    Notification.related_pod_id == pod.id,
                    Notification.notification_value == "POD_LOW_ATTENDANCE",
                    Notification.created_at >= twenty_four_hours_ago,
                )
            )

            existing_result = await db.execute(existing_notification_query)
            existing_notification = existing_result.scalar_one_or_none()

            if existing_notification:
                logger.info(
                    f"[파티 마감 임박 알림] 최근 24시간 내 이미 전송됨: owner_id={pod.owner_id}, pod_id={pod.id}, 기존 알림_id={existing_notification.id}, created_at={existing_notification.created_at}"
                )
                return  # 이미 보낸 알림이 있으면 다시 보내지 않음

            # 파티장 정보 조회
            pod_owner_id = getattr(pod, "owner_id", None)
            if pod_owner_id is None:
                return
            owner_query = select(User).where(User.id == pod_owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            if owner:
                owner_fcm_token = getattr(owner, "fcm_token", None)
                owner_id = getattr(owner, "id", None)
                pod_id = getattr(pod, "id", None)
                pod_title = getattr(pod, "title", "") or ""

                if owner_fcm_token and pod_id is not None and owner_id is not None:
                    await self.fcm_service.send_pod_low_attendance(
                        token=owner_fcm_token,
                        party_name=pod_title,
                        pod_id=pod_id,
                        db=db,
                        user_id=owner_id,
                        related_user_id=pod_owner_id,
                    )
                    logger.info(
                        f"파티 마감 임박 알림 전송 성공: owner_id={owner_id}, pod_id={pod_id}"
                    )
            else:
                logger.warning(f"파티장 FCM 토큰이 없음: owner_id={pod.owner_id}")

        except Exception as e:
            logger.error(f"파티 마감 임박 알림 처리 실패: pod_id={pod.id}, error={e}")

    async def _has_sent_canceled_soon_reminder(
        self, db: AsyncSession, user_id: int, pod_id: int
    ) -> bool:
        """파티 취소 임박 알림을 이미 보냈는지 확인 (최근 24시간 내)"""
        from datetime import datetime, timedelta, timezone

        from app.features.notifications.models import Notification

        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.related_pod_id == pod_id,
                Notification.notification_value == "POD_CANCELED_SOON",
                Notification.created_at >= twenty_four_hours_ago,  # 최근 24시간 내
            )
        )

        result = await db.execute(query)
        existing_notification = result.scalar_one_or_none()

        return existing_notification is not None

    async def _send_canceled_soon_reminders(self, db: AsyncSession):
        """파티 취소 임박 알림 (모집 중 상태 / 1시간 안에 시작하는 파티)"""
        now = datetime.now(timezone.utc)
        one_hour_later = now + timedelta(hours=1)
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # 1시간 안에 시작하는 모집 중인 파티들 조회
        # 조건: meeting_date + meeting_time이 now와 now + 1hour 사이
        # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)

        # 오늘 날짜이고 현재 시간 이후인 파티
        today_query = select(Pod).where(
            and_(
                Pod.meeting_date == today,
                Pod.meeting_time >= now.time(),
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper(),
            )
        )

        # 내일 날짜이고 1시간 이내인 파티
        tomorrow_query = select(Pod).where(
            and_(
                Pod.meeting_date == tomorrow,
                Pod.meeting_time <= one_hour_later.time(),
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper(),
            )
        )

        # 두 쿼리 결과 합치기
        today_result = await db.execute(today_query)
        tomorrow_result = await db.execute(tomorrow_query)
        today_pods = today_result.scalars().all()
        tomorrow_pods = tomorrow_result.scalars().all()

        # 모든 파티를 합치고, 실제로 1시간 안에 시작하는지 확인
        all_pods = list(today_pods) + list(tomorrow_pods)
        canceling_soon_pods = []

        for pod in all_pods:
            # meeting_date + meeting_time을 datetime으로 결합 (UTC로 해석)
            meeting_date = getattr(pod, "meeting_date", None)
            meeting_time = getattr(pod, "meeting_time", None)
            if meeting_date is None or meeting_time is None:
                continue
            meeting_datetime = datetime.combine(
                meeting_date, meeting_time, tzinfo=timezone.utc
            )

            # 1시간 안에 시작하는지 확인 (현재 시간 이후 ~ 1시간 후 이전)
            if now < meeting_datetime <= one_hour_later:
                canceling_soon_pods.append(pod)

        logger.info(
            f"파티 취소 임박 알림 대상: {len(canceling_soon_pods)}개 (1시간 안에 시작, 모집 중)"
        )

        for pod in canceling_soon_pods:
            # 모집 중이고 1시간 안에 시작하는 파티면 알림 전송 (중복 체크는 _send_canceled_soon_to_owner에서 처리)
            await self._send_canceled_soon_to_owner(db, pod)

    async def _send_canceled_soon_to_owner(self, db: AsyncSession, pod: Pod):
        """파티장에게 취소 임박 알림 전송"""
        try:
            pod_owner_id = getattr(pod, "owner_id", None)
            pod_id = getattr(pod, "id", None)
            if pod_owner_id is None or pod_id is None:
                return

            # 이미 오늘 같은 알림을 보냈는지 확인
            if await self._has_sent_canceled_soon_reminder(db, pod_owner_id, pod_id):
                logger.info(
                    f"파티 취소 임박 알림 이미 전송됨: owner_id={pod_owner_id}, pod_id={pod_id}"
                )
                return

            # 파티장 정보 조회
            owner_query = select(User).where(User.id == pod_owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            if owner:
                owner_fcm_token = getattr(owner, "fcm_token", None)
                owner_id = getattr(owner, "id", None)
                pod_title = getattr(pod, "title", "") or ""

                if owner_fcm_token and pod_id is not None and owner_id is not None:
                    await self.fcm_service.send_pod_canceled_soon(
                        token=owner_fcm_token,
                        party_name=pod_title,
                        pod_id=pod_id,
                        db=db,
                        user_id=owner_id,
                        related_user_id=pod_owner_id,
                    )
                    logger.info(
                        f"파티 취소 임박 알림 전송 성공: owner_id={owner_id}, pod_id={pod_id}"
                    )
                else:
                    logger.warning(f"파티장 FCM 토큰이 없음: owner_id={pod_owner_id}")
            else:
                logger.warning(f"파티장 정보를 찾을 수 없음: owner_id={pod_owner_id}")

        except Exception as e:
            logger.error(f"파티 취소 임박 알림 처리 실패: pod_id={pod.id}, error={e}")

    async def _cancel_unconfirmed_pods(self, db: AsyncSession):
        """모집 중인데 확정 안된 파티를 취소로 변경 (미팅 시간이 지난 경우)"""
        try:
            now = datetime.now(timezone.utc)

            # 모집 중인 모든 파티 조회 (날짜 제한 없이)
            # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
            query = select(Pod).where(
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper()
            )

            result = await db.execute(query)
            all_recruiting_pods = result.scalars().all()

            # meeting_datetime으로 정확히 비교하여 미팅 시간이 지난 파티만 필터링
            unconfirmed_pods = []
            for pod in all_recruiting_pods:
                # meeting_date + meeting_time을 datetime으로 결합 (UTC로 해석)
                meeting_date = getattr(pod, "meeting_date", None)
                meeting_time = getattr(pod, "meeting_time", None)
                if meeting_date is None or meeting_time is None:
                    continue
                meeting_datetime = datetime.combine(
                    meeting_date, meeting_time, tzinfo=timezone.utc
                )
                # 미팅 시간이 지났거나 같으면 취소 (<=)
                if meeting_datetime <= now:
                    unconfirmed_pods.append(pod)

            logger.info(f"확정 안된 모집 중 파티: {len(unconfirmed_pods)}개")

            for pod in unconfirmed_pods:
                try:
                    # enum 비교 시 안전하게 처리
                    # pod.status가 enum 객체이므로 .value로 실제 값을 가져옴
                    pod_status_value = (
                        pod.status.value.upper()
                        if hasattr(pod.status, "value")
                        else str(pod.status).upper()
                    )
                    if pod_status_value == PodStatus.RECRUITING.value.upper():
                        # 파티 상태를 CANCELED로 변경
                        pod.status = PodStatus.CANCELED
                        # 파티 비활성화 (소프트 삭제)
                        pod.is_del = True
                        logger.info(
                            f"파티 상태 변경: pod_id={pod.id}, title={pod.title}, meeting_date={pod.meeting_date}, meeting_time={pod.meeting_time}, RECRUITING → CANCELED, is_del=True"
                        )
                    else:
                        logger.warning(
                            f"파티 상태가 RECRUITING이 아님: pod_id={pod.id}, status={pod_status_value}"
                        )
                except Exception as e:
                    logger.error(f"파티 상태 변경 실패: pod_id={pod.id}, error={e}")

            # 변경사항 커밋
            if unconfirmed_pods:
                await db.commit()
                logger.info(f"파티 취소 완료: {len(unconfirmed_pods)}개")

        except Exception as e:
            logger.error(f"확정 안된 파티 취소 처리 중 오류: {e}")

    async def _has_sent_saved_pod_deadline(
        self, db: AsyncSession, user_id: int, pod_id: int
    ) -> bool:
        """좋아요한 파티 마감 임박 알림을 이미 보냈는지 확인 (최근 24시간 내)"""
        from datetime import datetime, timedelta, timezone

        from app.features.notifications.models import Notification

        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.related_pod_id == pod_id,
                Notification.notification_value == "SAVED_POD_DEADLINE",
                Notification.created_at >= twenty_four_hours_ago,  # 최근 24시간 내
            )
        )

        result = await db.execute(query)
        existing_notification = result.scalar_one_or_none()

        return existing_notification is not None

    async def _send_saved_pod_deadline_reminders(self, db: AsyncSession):
        """좋아요한 파티 마감 임박 알림"""
        tomorrow = date.today() + timedelta(days=1)

        # 내일 마감되는 파티들 조회
        # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
        query = select(Pod).where(
            and_(
                Pod.meeting_date == tomorrow,
                func.upper(Pod.status)
                == PodStatus.RECRUITING.value.upper(),  # 대소문자 무시 비교
            )
        )

        result = await db.execute(query)
        deadline_pods = result.scalars().all()

        for pod in deadline_pods:
            # 해당 파티를 좋아요한 사용자들 조회
            likes_query = (
                select(User)
                .join(PodLike, User.id == PodLike.user_id)
                .where(PodLike.pod_id == pod.id)
                .distinct()
            )

            likes_result = await db.execute(likes_query)
            liked_users = likes_result.scalars().all()

            # 각 좋아요한 사용자에게 알림 전송
            pod_id = getattr(pod, "id", None)
            pod_title = getattr(pod, "title", "") or ""
            pod_owner_id = getattr(pod, "owner_id", None)

            for user in liked_users:
                try:
                    user_id = getattr(user, "id", None)
                    if user_id is None or pod_id is None:
                        continue

                    # 이미 오늘 같은 알림을 보냈는지 확인
                    if await self._has_sent_saved_pod_deadline(db, user_id, pod_id):
                        logger.info(
                            f"좋아요한 파티 마감 임박 알림 이미 전송됨: user_id={user_id}, pod_id={pod_id}"
                        )
                        continue

                    fcm_token = getattr(user, "fcm_token", None)
                    if fcm_token:
                        await self.fcm_service.send_saved_pod_deadline(
                            token=fcm_token,
                            party_name=pod_title,
                            pod_id=pod_id,
                            db=db,
                            user_id=user_id,
                            related_user_id=pod_owner_id,
                        )
                        logger.info(
                            f"좋아요한 파티 마감 임박 알림 전송 성공: user_id={user_id}, pod_id={pod_id}"
                        )
                    else:
                        logger.warning(f"FCM 토큰이 없는 사용자: user_id={user.id}")

                except Exception as e:
                    logger.error(
                        f"좋아요한 파티 마감 임박 알림 전송 실패: user_id={user.id}, error={e}"
                    )

    async def _update_completed_pods_to_closed(self, db: AsyncSession):
        """확정(COMPLETED) 상태인 파티가 미팅일 다음 날부터 종료(CLOSED)로 변경"""
        try:
            today = date.today()

            # 미팅일이 오늘보다 이전인 COMPLETED 상태인 파티들 조회 (미팅일 다음 날부터 CLOSED로 변경)
            # enum 비교 시 안전하게 처리 (DB에 소문자 값이 남아있을 수 있음)
            query = select(Pod).where(
                and_(
                    Pod.meeting_date
                    < today,  # 미팅일이 오늘보다 이전 (미팅일 다음 날부터)
                    func.upper(Pod.status)
                    == PodStatus.COMPLETED.value.upper(),  # 대소문자 무시 비교
                )
            )

            result = await db.execute(query)
            completed_pods = result.scalars().all()

            logger.info(f"미팅일이 지난 확정 파티: {len(completed_pods)}개")

            # 각 파티 상태를 CLOSED로 변경 및 채팅방 삭제
            for pod in completed_pods:
                try:
                    pod_id = getattr(pod, "id", None)
                    pod_title = getattr(pod, "title", "") or ""
                    pod_meeting_date = getattr(pod, "meeting_date", None)

                    if pod_id is None:
                        continue

                    # 파티 상태를 CLOSED로 변경
                    stmt = (
                        update(Pod)
                        .where(Pod.id == pod_id)
                        .values(status=PodStatus.CLOSED.value)
                    )
                    await db.execute(stmt)
                    await db.commit()

                    logger.info(
                        f"파티 상태 변경: pod_id={pod_id}, title={pod_title}, meeting_date={pod_meeting_date}, COMPLETED → CLOSED"
                    )

                except Exception as e:
                    logger.error(f"파티 상태 변경 실패: pod_id={pod.id}, error={e}")

            # 변경사항 커밋
            await db.commit()
            logger.info(f"파티 상태 변경 완료: {len(completed_pods)}개")

        except Exception as e:
            logger.error(f"파티 상태 자동 변경 처리 실패: {e}")
            await db.rollback()


# 스케줄러 인스턴스
scheduler = SchedulerService()


async def run_daily_scheduler():
    """매일 아침 10시에 실행되는 스케줄러 (리뷰, 마감 임박 알림)"""
    while True:
        try:
            # 다음 아침 10시까지 대기
            await wait_until_10am()

            logger.info("일일 스케줄러 실행 시작 (리뷰, 마감 임박 알림)")
            await scheduler.check_review_reminders()
            logger.info("일일 스케줄러 실행 완료")

        except Exception as e:
            logger.error(f"일일 스케줄러 실행 중 오류: {e}")
            # 오류 발생 시 1시간 후 재시도
            await asyncio.sleep(60 * 60)


async def run_hourly_scheduler():
    """1시간마다 실행되는 스케줄러 (마감 임박 알림만)"""
    while True:
        try:
            logger.info("시간별 스케줄러 실행 시작 (마감 임박 알림)")
            await scheduler.check_deadline_reminders()
            logger.info("시간별 스케줄러 실행 완료")

            # 1시간 대기
            await asyncio.sleep(60 * 60)

        except Exception as e:
            logger.error(f"시간별 스케줄러 실행 중 오류: {e}")
            # 오류 발생 시 10분 후 재시도
            await asyncio.sleep(10 * 60)


async def run_5min_scheduler():
    """5분마다 실행되는 스케줄러 (파티 시작 임박 알림)"""
    while True:
        try:
            logger.info("5분 스케줄러 실행 시작 (파티 시작 임박 알림)")
            await scheduler.check_start_soon_reminders()
            logger.info("5분 스케줄러 실행 완료")

            # 5분 대기
            await asyncio.sleep(5 * 60)

        except Exception as e:
            logger.error(f"5분 스케줄러 실행 중 오류: {e}")
            # 오류 발생 시 2분 후 재시도
            await asyncio.sleep(2 * 60)


async def wait_until_10am():
    """다음 아침 10시까지 대기"""
    now = datetime.now(timezone.utc)

    # 오늘 아침 10시
    today_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)

    # 이미 오늘 10시가 지났다면 내일 10시까지 대기
    if now >= today_10am:
        tomorrow_10am = today_10am + timedelta(days=1)
        wait_seconds = (tomorrow_10am - now).total_seconds()
    else:
        # 아직 오늘 10시가 안 지났다면 오늘 10시까지 대기
        wait_seconds = (today_10am - now).total_seconds()

    logger.info(f"다음 스케줄러 실행까지 {wait_seconds / 3600:.1f}시간 대기")
    await asyncio.sleep(wait_seconds)


# 스케줄러 시작 함수
async def start_scheduler():
    """스케줄러 시작"""
    logger.info("스케줄러 시작:")
    logger.info("- 매일 아침 10시: 리뷰 유도 알림")
    logger.info("- 5분마다: 파티 시작 임박 알림")
    logger.info("- 1시간마다: 마감 임박 알림")

    # 세 개 스케줄러를 병렬로 실행
    await asyncio.gather(
        run_daily_scheduler(), run_5min_scheduler(), run_hourly_scheduler()
    )
