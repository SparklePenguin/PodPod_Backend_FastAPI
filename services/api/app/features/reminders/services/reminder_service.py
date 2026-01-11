"""알림 리마인더 서비스 - 스케줄러에서 호출되는 알림 비즈니스 로직"""

import logging
from datetime import date, datetime, timedelta, timezone

from app.core.services.fcm_service import FCMService
from app.features.notifications.models import Notification
from app.features.pods.models import Pod, PodLike, PodMember, PodRating, PodStatus
from app.features.users.models import User
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# 상수 정의
class ReminderConstants:
    """리마인더 관련 상수"""

    REVIEW_REMINDER_DAY = "REVIEW_REMINDER_DAY"
    REVIEW_REMINDER_WEEK = "REVIEW_REMINDER_WEEK"
    POD_START_SOON = "POD_START_SOON"
    POD_LOW_ATTENDANCE = "POD_LOW_ATTENDANCE"
    POD_CANCELED_SOON = "POD_CANCELED_SOON"
    SAVED_POD_DEADLINE = "SAVED_POD_DEADLINE"

    # 시간 설정
    START_SOON_HOURS = 1  # 시작 임박 알림 (1시간 전)
    DEADLINE_HOURS = 24  # 마감 임박 알림 (24시간 전)
    DUPLICATE_CHECK_HOURS = 24  # 중복 체크 시간 (24시간)


class ReminderService:
    """알림 리마인더 서비스

    스케줄러에서 호출되어 각종 알림을 체크하고 전송합니다.
    """

    def __init__(self):
        self.fcm_service = FCMService()

    # ==================== 공통 헬퍼 메서드 ====================

    async def _has_sent_reminder(
        self,
        db: AsyncSession,
        user_id: int,
        pod_id: int,
        notification_type: str,
        hours: int = 24,
    ) -> bool:
        """특정 알림이 이미 전송되었는지 확인

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            pod_id: 파티 ID
            notification_type: 알림 타입
            hours: 중복 체크 시간 (기본 24시간)
        """
        check_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.notification_value == notification_type,
                Notification.created_at >= check_time,
                or_(
                    Notification.related_pod_id == pod_id,
                    Notification.related_id == str(pod_id),
                ),
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def _get_pod_participants(
        self, db: AsyncSession, pod: Pod, include_owner: bool = True
    ) -> list[User]:
        """파티 참여자 목록 조회

        Args:
            db: 데이터베이스 세션
            pod: 파티 객체
            include_owner: 파티장 포함 여부
        """
        # 멤버 조회
        participants_query = (
            select(User)
            .join(PodMember, User.id == PodMember.user_id)
            .where(PodMember.pod_id == pod.id)
            .distinct()
        )

        result = await db.execute(participants_query)
        participants = list(result.scalars().all())

        # 파티장 추가
        if include_owner:
            owner_query = select(User).where(User.id == pod.owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            if owner and owner not in participants:
                participants.append(owner)

        return participants

    async def _get_pods_by_status_and_date(
        self,
        db: AsyncSession,
        status: PodStatus,
        target_date: date,
    ) -> list[Pod]:
        """상태와 날짜로 파티 조회"""
        query = select(Pod).where(
            and_(
                Pod.meeting_date == target_date,
                func.upper(Pod.status) == status.value.upper(),
            )
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    # ==================== 리뷰 리마인더 ====================

    async def send_review_reminders(self, db: AsyncSession):
        """리뷰 유도 알림 전송 (1일 전, 1주일 전)"""
        try:
            # 1일 전 모임 리뷰 알림
            await self._send_day_review_reminders(db)

            # 1주일 전 모임 리뷰 리마인드 (미작성자만)
            await self._send_week_review_reminders(db)

        except Exception as e:
            logger.error(f"리뷰 리마인더 전송 중 오류: {e}")

    async def _send_day_review_reminders(self, db: AsyncSession):
        """1일 전 모임 리뷰 유도 알림"""
        yesterday = date.today() - timedelta(days=1)
        completed_pods = await self._get_pods_by_status_and_date(
            db, PodStatus.COMPLETED, yesterday
        )

        for pod in completed_pods:
            await self._send_review_to_participants(
                db, pod, ReminderConstants.REVIEW_REMINDER_DAY
            )

    async def _send_week_review_reminders(self, db: AsyncSession):
        """1주일 전 모임 리뷰 리마인드 (미작성자만)"""
        week_ago = date.today() - timedelta(days=7)
        completed_pods = await self._get_pods_by_status_and_date(
            db, PodStatus.COMPLETED, week_ago
        )

        for pod in completed_pods:
            await self._send_review_to_non_reviewers(
                db, pod, ReminderConstants.REVIEW_REMINDER_WEEK
            )

    async def _send_review_to_participants(
        self, db: AsyncSession, pod: Pod, reminder_type: str
    ):
        """모든 참여자에게 리뷰 유도 알림 전송"""
        try:
            participants = await self._get_pod_participants(db, pod, include_owner=True)

            for participant in participants:
                await self._send_review_notification(
                    db, participant, pod, reminder_type
                )

        except Exception as e:
            logger.error(f"참여자 리뷰 알림 전송 실패: pod_id={pod.id}, error={e}")

    async def _send_review_to_non_reviewers(
        self, db: AsyncSession, pod: Pod, reminder_type: str
    ):
        """리뷰 미작성자에게만 리마인드 알림 전송 (파티장 제외)"""
        try:
            participants = await self._get_pod_participants(
                db, pod, include_owner=False
            )

            # 리뷰 작성자 ID 조회
            reviewers_query = select(PodRating.user_id).where(PodRating.pod_id == pod.id)
            reviewers_result = await db.execute(reviewers_query)
            reviewer_ids = {row[0] for row in reviewers_result.all()}

            for participant in participants:
                participant_id = getattr(participant, "id", None)
                if participant_id is None:
                    continue

                # 파티장 제외
                if participant_id == pod.owner_id:
                    continue

                # 리뷰 작성자 제외
                if participant_id in reviewer_ids:
                    continue

                await self._send_review_notification(
                    db, participant, pod, reminder_type
                )

        except Exception as e:
            logger.error(f"미작성자 리뷰 알림 전송 실패: pod_id={pod.id}, error={e}")

    async def _send_review_notification(
        self, db: AsyncSession, user: User, pod: Pod, reminder_type: str
    ):
        """개별 사용자에게 리뷰 알림 전송"""
        try:
            user_id = getattr(user, "id", None)
            pod_id = getattr(pod, "id", None)
            if user_id is None or pod_id is None:
                return

            # 중복 체크
            if await self._has_sent_reminder(db, user_id, pod_id, reminder_type):
                logger.info(
                    f"{reminder_type} 알림 이미 전송됨: user_id={user_id}, pod_id={pod_id}"
                )
                return

            fcm_token = getattr(user, "fcm_token", None)
            if not fcm_token:
                logger.warning(f"FCM 토큰 없음: user_id={user_id}")
                return

            pod_title = getattr(pod, "title", "") or ""

            if reminder_type == ReminderConstants.REVIEW_REMINDER_DAY:
                await self.fcm_service.send_review_reminder_day(
                    token=fcm_token,
                    party_name=pod_title,
                    pod_id=pod_id,
                    db=db,
                    user_id=user_id,
                )
            elif reminder_type == ReminderConstants.REVIEW_REMINDER_WEEK:
                await self.fcm_service.send_review_reminder_week(
                    token=fcm_token,
                    party_name=pod_title,
                    pod_id=pod_id,
                    db=db,
                    user_id=user_id,
                )

            logger.info(
                f"{reminder_type} 알림 전송 성공: user_id={user_id}, pod_id={pod_id}"
            )

        except Exception as e:
            logger.error(f"리뷰 알림 전송 실패: user_id={user.id}, error={e}")

    # ==================== 시작 임박 알림 ====================

    async def send_start_soon_reminders(self, db: AsyncSession):
        """파티 시작 1시간 전 알림"""
        try:
            now = datetime.now(timezone.utc)
            one_hour_later = now + timedelta(hours=ReminderConstants.START_SOON_HOURS)

            # 1시간 후 시작하는 확정된 파티 조회
            query = select(Pod).where(
                and_(
                    Pod.meeting_date == now.date(),
                    Pod.meeting_time >= now.time(),
                    Pod.meeting_time <= one_hour_later.time(),
                    func.upper(Pod.status) == PodStatus.COMPLETED.value.upper(),
                )
            )

            result = await db.execute(query)
            starting_soon_pods = result.scalars().all()

            logger.info(f"파티 시작 임박 알림 대상: {len(starting_soon_pods)}개")

            for pod in starting_soon_pods:
                await self._send_start_soon_to_participants(db, pod)

        except Exception as e:
            logger.error(f"시작 임박 알림 전송 중 오류: {e}")

    async def _send_start_soon_to_participants(self, db: AsyncSession, pod: Pod):
        """참여자들에게 시작 임박 알림 전송"""
        try:
            participants = await self._get_pod_participants(db, pod, include_owner=True)

            for participant in participants:
                await self._send_start_soon_notification(db, participant, pod)

        except Exception as e:
            logger.error(f"시작 임박 알림 처리 실패: pod_id={pod.id}, error={e}")

    async def _send_start_soon_notification(
        self, db: AsyncSession, user: User, pod: Pod
    ):
        """개별 사용자에게 시작 임박 알림 전송"""
        try:
            user_id = getattr(user, "id", None)
            pod_id = getattr(pod, "id", None)
            if user_id is None or pod_id is None:
                return

            # 중복 체크
            if await self._has_sent_reminder(
                db, user_id, pod_id, ReminderConstants.POD_START_SOON
            ):
                logger.info(
                    f"시작 임박 알림 이미 전송됨: user_id={user_id}, pod_id={pod_id}"
                )
                return

            fcm_token = getattr(user, "fcm_token", None)
            if not fcm_token:
                logger.warning(f"FCM 토큰 없음: user_id={user_id}")
                return

            pod_title = getattr(pod, "title", "") or ""
            pod_owner_id = getattr(pod, "owner_id", None)

            await self.fcm_service.send_pod_start_soon(
                token=fcm_token,
                party_name=pod_title,
                pod_id=pod_id,
                db=db,
                user_id=user_id,
                related_user_id=pod_owner_id,
            )

            logger.info(
                f"시작 임박 알림 전송 성공: user_id={user_id}, pod_id={pod_id}"
            )

        except Exception as e:
            logger.error(f"시작 임박 알림 전송 실패: user_id={user.id}, error={e}")

    # ==================== 마감 임박 알림 ====================

    async def send_deadline_reminders(self, db: AsyncSession):
        """마감 임박 알림 전송"""
        try:
            # 파티장에게 인원 부족 알림
            await self._send_low_attendance_reminders(db)

            # 좋아요한 파티 마감 임박 알림
            await self._send_saved_pod_deadline_reminders(db)

        except Exception as e:
            logger.error(f"마감 임박 알림 전송 중 오류: {e}")

    async def _send_low_attendance_reminders(self, db: AsyncSession):
        """파티 마감 임박 알림 (24시간 안에 마감되는 모집 중 파티)"""
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=ReminderConstants.DEADLINE_HOURS)

        # 모집 중인 파티 조회 (오늘/내일)
        closing_soon_pods = await self._get_closing_soon_pods(db, now, deadline)

        logger.info(f"마감 임박 알림 대상: {len(closing_soon_pods)}개")

        for pod in closing_soon_pods:
            await self._send_low_attendance_to_owner(db, pod)

    async def _get_closing_soon_pods(
        self, db: AsyncSession, now: datetime, deadline: datetime
    ) -> list[Pod]:
        """마감 임박 파티 조회 (시간 범위 내)"""
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # 오늘/내일 모집 중인 파티 조회
        query = select(Pod).where(
            and_(
                or_(Pod.meeting_date == today, Pod.meeting_date == tomorrow),
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper(),
            )
        )

        result = await db.execute(query)
        all_pods = result.scalars().all()

        # 시간 범위 필터링
        closing_soon = []
        for pod in all_pods:
            meeting_date = getattr(pod, "meeting_date", None)
            meeting_time = getattr(pod, "meeting_time", None)
            if meeting_date is None or meeting_time is None:
                continue

            meeting_datetime = datetime.combine(
                meeting_date, meeting_time, tzinfo=timezone.utc
            )
            if now <= meeting_datetime <= deadline:
                closing_soon.append(pod)

        return closing_soon

    async def _send_low_attendance_to_owner(self, db: AsyncSession, pod: Pod):
        """파티장에게 마감 임박 알림 전송"""
        try:
            pod_owner_id = getattr(pod, "owner_id", None)
            pod_id = getattr(pod, "id", None)
            if pod_owner_id is None or pod_id is None:
                return

            # 중복 체크
            if await self._has_sent_reminder(
                db, pod_owner_id, pod_id, ReminderConstants.POD_LOW_ATTENDANCE
            ):
                logger.info(
                    f"마감 임박 알림 이미 전송됨: owner_id={pod_owner_id}, pod_id={pod_id}"
                )
                return

            # 파티장 조회
            owner_query = select(User).where(User.id == pod_owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            if not owner:
                logger.warning(f"파티장 정보 없음: owner_id={pod_owner_id}")
                return

            fcm_token = getattr(owner, "fcm_token", None)
            if not fcm_token:
                logger.warning(f"파티장 FCM 토큰 없음: owner_id={pod_owner_id}")
                return

            pod_title = getattr(pod, "title", "") or ""

            await self.fcm_service.send_pod_low_attendance(
                token=fcm_token,
                party_name=pod_title,
                pod_id=pod_id,
                db=db,
                user_id=pod_owner_id,
                related_user_id=pod_owner_id,
            )

            logger.info(
                f"마감 임박 알림 전송 성공: owner_id={pod_owner_id}, pod_id={pod_id}"
            )

        except Exception as e:
            logger.error(f"마감 임박 알림 전송 실패: pod_id={pod.id}, error={e}")

    async def _send_saved_pod_deadline_reminders(self, db: AsyncSession):
        """좋아요한 파티 마감 임박 알림"""
        tomorrow = date.today() + timedelta(days=1)

        # 내일 마감되는 모집 중인 파티 조회
        query = select(Pod).where(
            and_(
                Pod.meeting_date == tomorrow,
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper(),
            )
        )

        result = await db.execute(query)
        deadline_pods = result.scalars().all()

        for pod in deadline_pods:
            await self._send_saved_deadline_to_likers(db, pod)

    async def _send_saved_deadline_to_likers(self, db: AsyncSession, pod: Pod):
        """좋아요한 사용자들에게 마감 임박 알림 전송"""
        try:
            pod_id = getattr(pod, "id", None)
            pod_title = getattr(pod, "title", "") or ""
            pod_owner_id = getattr(pod, "owner_id", None)

            if pod_id is None:
                return

            # 좋아요한 사용자 조회
            likes_query = (
                select(User)
                .join(PodLike, User.id == PodLike.user_id)
                .where(PodLike.pod_id == pod_id)
                .distinct()
            )

            likes_result = await db.execute(likes_query)
            liked_users = likes_result.scalars().all()

            for user in liked_users:
                try:
                    user_id = getattr(user, "id", None)
                    if user_id is None:
                        continue

                    # 중복 체크
                    if await self._has_sent_reminder(
                        db, user_id, pod_id, ReminderConstants.SAVED_POD_DEADLINE
                    ):
                        continue

                    fcm_token = getattr(user, "fcm_token", None)
                    if not fcm_token:
                        continue

                    await self.fcm_service.send_saved_pod_deadline(
                        token=fcm_token,
                        party_name=pod_title,
                        pod_id=pod_id,
                        db=db,
                        user_id=user_id,
                        related_user_id=pod_owner_id,
                    )

                    logger.info(
                        f"좋아요 파티 마감 알림 전송: user_id={user_id}, pod_id={pod_id}"
                    )

                except Exception as e:
                    logger.error(f"좋아요 파티 마감 알림 실패: user_id={user.id}, error={e}")

        except Exception as e:
            logger.error(f"좋아요 파티 마감 알림 처리 실패: pod_id={pod.id}, error={e}")

    # ==================== 취소 임박 알림 ====================

    async def send_canceled_soon_reminders(self, db: AsyncSession):
        """파티 취소 임박 알림 (1시간 안에 시작하는 모집 중 파티)"""
        try:
            now = datetime.now(timezone.utc)
            one_hour_later = now + timedelta(hours=ReminderConstants.START_SOON_HOURS)

            canceling_soon_pods = await self._get_canceling_soon_pods(
                db, now, one_hour_later
            )

            logger.info(f"취소 임박 알림 대상: {len(canceling_soon_pods)}개")

            for pod in canceling_soon_pods:
                await self._send_canceled_soon_to_owner(db, pod)

        except Exception as e:
            logger.error(f"취소 임박 알림 전송 중 오류: {e}")

    async def _get_canceling_soon_pods(
        self, db: AsyncSession, now: datetime, deadline: datetime
    ) -> list[Pod]:
        """취소 임박 파티 조회 (1시간 이내 시작하는 모집 중 파티)"""
        today = now.date()
        tomorrow = today + timedelta(days=1)

        query = select(Pod).where(
            and_(
                or_(Pod.meeting_date == today, Pod.meeting_date == tomorrow),
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper(),
            )
        )

        result = await db.execute(query)
        all_pods = result.scalars().all()

        canceling_soon = []
        for pod in all_pods:
            meeting_date = getattr(pod, "meeting_date", None)
            meeting_time = getattr(pod, "meeting_time", None)
            if meeting_date is None or meeting_time is None:
                continue

            meeting_datetime = datetime.combine(
                meeting_date, meeting_time, tzinfo=timezone.utc
            )
            if now < meeting_datetime <= deadline:
                canceling_soon.append(pod)

        return canceling_soon

    async def _send_canceled_soon_to_owner(self, db: AsyncSession, pod: Pod):
        """파티장에게 취소 임박 알림 전송"""
        try:
            pod_owner_id = getattr(pod, "owner_id", None)
            pod_id = getattr(pod, "id", None)
            if pod_owner_id is None or pod_id is None:
                return

            # 중복 체크
            if await self._has_sent_reminder(
                db, pod_owner_id, pod_id, ReminderConstants.POD_CANCELED_SOON
            ):
                logger.info(
                    f"취소 임박 알림 이미 전송됨: owner_id={pod_owner_id}, pod_id={pod_id}"
                )
                return

            # 파티장 조회
            owner_query = select(User).where(User.id == pod_owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            if not owner:
                return

            fcm_token = getattr(owner, "fcm_token", None)
            if not fcm_token:
                logger.warning(f"파티장 FCM 토큰 없음: owner_id={pod_owner_id}")
                return

            pod_title = getattr(pod, "title", "") or ""

            await self.fcm_service.send_pod_canceled_soon(
                token=fcm_token,
                party_name=pod_title,
                pod_id=pod_id,
                db=db,
                user_id=pod_owner_id,
                related_user_id=pod_owner_id,
            )

            logger.info(
                f"취소 임박 알림 전송 성공: owner_id={pod_owner_id}, pod_id={pod_id}"
            )

        except Exception as e:
            logger.error(f"취소 임박 알림 전송 실패: pod_id={pod.id}, error={e}")
