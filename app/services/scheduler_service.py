from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.pod import Pod, PodMember, PodLike
from app.models.pod.pod_rating import PodRating
from app.models.pod.pod_status import PodStatus
from app.models.user import User
from app.services.fcm_service import FCMService
from app.core.database import get_db
from datetime import datetime, date, timedelta, time
import asyncio
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """스케줄러 서비스 - 주기적인 작업 처리"""

    def __init__(self):
        self.fcm_service = FCMService()

    async def check_review_reminders(self):
        """모임 종료 후 리뷰 유도 알림 체크 (1시간마다)"""
        try:
            # 데이터베이스 세션 생성
            async for db in get_db():
                try:
                    # 파티 상태 자동 변경 (미팅일이 된 확정 파티를 종료로)
                    await self._update_completed_pods_to_closed(db)

                    # 1일 전 모임들 조회 (REVIEW_REMINDER_DAY)
                    await self._send_day_reminders(db)

                    # 1주일 전 모임들 조회 (REVIEW_REMINDER_WEEK)
                    await self._send_week_reminders(db)

                    # 파티 마감 임박 알림 (24시간 전 + 인원 부족)
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
            async for db in get_db():
                try:
                    # 파티 상태 자동 변경 (미팅일이 지난 확정 파티를 종료로)
                    await self._update_completed_pods_to_closed(db)

                    # 파티 시작 임박 알림 (1시간 전)
                    await self._send_start_soon_reminders(db)

                finally:
                    await db.close()

        except Exception as e:
            logger.error(f"파티 시작 임박 알림 체크 중 오류: {e}")

    async def check_deadline_reminders(self):
        """마감 임박 알림 체크 (1시간마다)"""
        try:
            # 데이터베이스 세션 생성
            async for db in get_db():
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
        from app.models.notification import Notification

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
        from app.models.notification import Notification

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
        query = select(Pod).where(
            and_(
                Pod.meeting_date == yesterday,
                Pod.status.in_(["CONFIRMED", "COMPLETED"]),  # 확정되거나 완료된 모임
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
        query = select(Pod).where(
            and_(
                Pod.meeting_date == week_ago, Pod.status.in_(["CONFIRMED", "COMPLETED"])
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
            participants = result.scalars().all()

            if owner and owner not in participants:
                participants.append(owner)

            # 각 참여자에게 알림 전송
            for participant in participants:
                try:
                    # 이미 오늘 같은 알림을 보냈는지 확인
                    if await self._has_sent_review_reminder(
                        db, participant.id, pod.id, reminder_type
                    ):
                        logger.info(
                            f"{reminder_type} 알림 이미 전송됨: user_id={participant.id}, pod_id={pod.id}"
                        )
                        continue

                    if participant.fcm_token:
                        if reminder_type == "REVIEW_REMINDER_DAY":
                            await self.fcm_service.send_review_reminder_day(
                                token=participant.fcm_token,
                                party_name=pod.title,
                                pod_id=pod.id,
                                db=db,
                                user_id=participant.id,
                            )
                        elif reminder_type == "REVIEW_REMINDER_WEEK":
                            await self.fcm_service.send_review_reminder_week(
                                token=participant.fcm_token,
                                party_name=pod.title,
                                pod_id=pod.id,
                                db=db,
                                user_id=participant.id,
                            )

                        logger.info(
                            f"{reminder_type} 알림 전송 성공: user_id={participant.id}, pod_id={pod.id}"
                        )
                    else:
                        logger.warning(
                            f"FCM 토큰이 없는 사용자: user_id={participant.id}"
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
        """리뷰 미작성자들에게만 리마인드 알림 전송"""
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
            participants = result.scalars().all()

            if owner and owner not in participants:
                participants.append(owner)

            # 리뷰를 작성한 사용자들 조회
            reviewers_query = select(PodRating.user_id).where(
                PodRating.pod_id == pod.id
            )
            reviewers_result = await db.execute(reviewers_query)
            reviewer_ids = {row[0] for row in reviewers_result.all()}

            # 리뷰 미작성자들에게만 알림 전송
            for participant in participants:
                if participant.id not in reviewer_ids:
                    try:
                        if participant.fcm_token:
                            await self.fcm_service.send_review_reminder_week(
                                token=participant.fcm_token,
                                party_name=pod.title,
                                pod_id=pod.id,
                                db=db,
                                user_id=participant.id,
                            )
                            logger.info(
                                f"리뷰 미작성자 리마인드 알림 전송 성공: user_id={participant.id}, pod_id={pod.id}"
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
        now = datetime.now()
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
            logger.info(
                f"- 파티 ID: {pod.id}, 제목: {pod.title}, 시간: {pod.meeting_time}, 상태: {pod.status}"
            )

        # 파티 88번 특별 조회
        pod88_query = select(Pod).where(Pod.id == 88)
        pod88_result = await db.execute(pod88_query)
        pod88 = pod88_result.scalar_one_or_none()

        if pod88:
            logger.info(
                f"파티 88번 정보: ID={pod88.id}, 제목={pod88.title}, 날짜={pod88.meeting_date}, 시간={pod88.meeting_time}, 상태={pod88.status}"
            )
        else:
            logger.info("파티 88번을 찾을 수 없습니다.")

        # 1시간 후 시작하는 모임들 조회
        query = select(Pod).where(
            and_(
                Pod.meeting_date == now.date(),
                Pod.meeting_time >= now.time(),
                Pod.meeting_time <= one_hour_later.time(),
                Pod.status.in_(["CONFIRMED", "COMPLETED"]),  # 확정되거나 완료된 모임
            )
        )

        result = await db.execute(query)
        starting_soon_pods = result.scalars().all()

        logger.info(f"파티 시작 임박 알림 대상: {len(starting_soon_pods)}개")
        for pod in starting_soon_pods:
            logger.info(
                f"- 파티 ID: {pod.id}, 제목: {pod.title}, 시간: {pod.meeting_time}, 상태: {pod.status}"
            )

        for pod in starting_soon_pods:
            await self._send_start_soon_to_participants(db, pod)

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
            participants = result.scalars().all()

            if owner and owner not in participants:
                participants.append(owner)

            # 각 참여자에게 알림 전송
            for participant in participants:
                try:
                    # 이미 오늘 같은 알림을 보냈는지 확인
                    if await self._has_sent_start_soon_reminder(
                        db, participant.id, pod.id
                    ):
                        logger.info(
                            f"파티 시작 임박 알림 이미 전송됨: user_id={participant.id}, pod_id={pod.id}"
                        )
                        continue

                    if participant.fcm_token:
                        await self.fcm_service.send_pod_start_soon(
                            token=participant.fcm_token,
                            party_name=pod.title,
                            pod_id=pod.id,
                            db=db,
                            user_id=participant.id,
                        )
                        logger.info(
                            f"파티 시작 임박 알림 전송 성공: user_id={participant.id}, pod_id={pod.id}"
                        )
                    else:
                        logger.warning(
                            f"FCM 토큰이 없는 사용자: user_id={participant.id}"
                        )

                except Exception as e:
                    logger.error(
                        f"파티 시작 임박 알림 전송 실패: user_id={participant.id}, error={e}"
                    )

        except Exception as e:
            logger.error(f"파티 시작 임박 알림 처리 실패: pod_id={pod.id}, error={e}")

    async def _send_low_attendance_reminders(self, db: AsyncSession):
        """파티 마감 임박 + 인원 부족 알림"""
        now = datetime.now()
        twenty_four_hours_later = now + timedelta(hours=24)

        # 24시간 후 마감되는 모임들 조회
        query = select(Pod).where(
            and_(
                Pod.meeting_date == twenty_four_hours_later.date(),
                Pod.status == "RECRUITING",  # 모집 중인 모임만
            )
        )

        result = await db.execute(query)
        closing_soon_pods = result.scalars().all()

        for pod in closing_soon_pods:
            # 현재 참여자 수 확인
            participants_query = select(PodMember.user_id).where(
                PodMember.pod_id == pod.id
            )
            participants_result = await db.execute(participants_query)
            participant_count = len(participants_result.all()) + 1  # 파티장 포함

            # 인원 부족 체크 (예: 정원의 70% 미만)
            if participant_count < (pod.capacity * 0.7):
                await self._send_low_attendance_to_owner(db, pod)

    async def _send_low_attendance_to_owner(self, db: AsyncSession, pod: Pod):
        """파티장에게 인원 부족 알림 전송"""
        try:
            # 파티장 정보 조회
            owner_query = select(User).where(User.id == pod.owner_id)
            owner_result = await db.execute(owner_query)
            owner = owner_result.scalar_one_or_none()

            if owner and owner.fcm_token:
                await self.fcm_service.send_pod_low_attendance(
                    token=owner.fcm_token,
                    party_name=pod.title,
                    pod_id=pod.id,
                    db=db,
                    user_id=owner.id,
                )
                logger.info(
                    f"파티 마감 임박 알림 전송 성공: owner_id={owner.id}, pod_id={pod.id}"
                )
            else:
                logger.warning(f"파티장 FCM 토큰이 없음: owner_id={pod.owner_id}")

        except Exception as e:
            logger.error(f"파티 마감 임박 알림 처리 실패: pod_id={pod.id}, error={e}")

    async def _send_saved_pod_deadline_reminders(self, db: AsyncSession):
        """좋아요한 파티 마감 임박 알림"""
        tomorrow = date.today() + timedelta(days=1)

        # 내일 마감되는 파티들 조회
        query = select(Pod).where(
            and_(
                Pod.meeting_date == tomorrow,
                Pod.status == "RECRUITING",  # 모집 중인 모임만
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
            for user in liked_users:
                try:
                    if user.fcm_token:
                        await self.fcm_service.send_saved_pod_deadline(
                            token=user.fcm_token,
                            party_name=pod.title,
                            pod_id=pod.id,
                            db=db,
                            user_id=user.id,
                        )
                        logger.info(
                            f"좋아요한 파티 마감 임박 알림 전송 성공: user_id={user.id}, pod_id={pod.id}"
                        )
                    else:
                        logger.warning(f"FCM 토큰이 없는 사용자: user_id={user.id}")

                except Exception as e:
                    logger.error(
                        f"좋아요한 파티 마감 임박 알림 전송 실패: user_id={user.id}, error={e}"
                    )

    async def _update_completed_pods_to_closed(self, db: AsyncSession):
        """확정(COMPLETED) 상태인 파티가 미팅일이 지나면 종료(CLOSED)로 변경"""
        try:
            today = date.today()

            # 미팅일이 오늘 이하이고 COMPLETED 상태인 파티들 조회 (과거에 패스된 것도 포함)
            query = select(Pod).where(
                and_(
                    Pod.meeting_date <= today,
                    Pod.status == PodStatus.COMPLETED,
                )
            )

            result = await db.execute(query)
            completed_pods = result.scalars().all()

            logger.info(f"미팅일이 지난 확정 파티: {len(completed_pods)}개")

            # 각 파티 상태를 CLOSED로 변경
            for pod in completed_pods:
                try:
                    pod.status = PodStatus.CLOSED
                    logger.info(
                        f"파티 상태 변경: pod_id={pod.id}, title={pod.title}, meeting_date={pod.meeting_date}, COMPLETED → CLOSED"
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
    now = datetime.now()

    # 오늘 아침 10시
    today_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)

    # 이미 오늘 10시가 지났다면 내일 10시까지 대기
    if now >= today_10am:
        tomorrow_10am = today_10am + timedelta(days=1)
        wait_seconds = (tomorrow_10am - now).total_seconds()
    else:
        # 아직 오늘 10시가 안 지났다면 오늘 10시까지 대기
        wait_seconds = (today_10am - now).total_seconds()

    logger.info(f"다음 스케줄러 실행까지 {wait_seconds/3600:.1f}시간 대기")
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
