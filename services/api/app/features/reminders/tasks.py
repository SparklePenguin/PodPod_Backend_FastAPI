"""리마인더 태스크 - 스케줄러에 등록할 작업들 정의

이 모듈에서 스케줄러에 등록할 작업들을 정의하고 등록합니다.
"""

import logging

from app.core.database import get_session
from app.core.scheduler import Scheduler

from .services import ReminderService, StatusUpdateService

logger = logging.getLogger(__name__)


def create_services() -> tuple[ReminderService, StatusUpdateService]:
    """서비스 인스턴스 생성"""
    return ReminderService(), StatusUpdateService()


def register_scheduler_tasks(scheduler: Scheduler) -> None:
    """스케줄러에 리마인더 작업들 등록"""
    reminder_service, status_update_service = create_services()

    # 일일 작업 (매일 오전 10시)
    async def daily_tasks() -> None:
        """일일 작업: 상태 업데이트 + 리뷰 알림 + 마감 알림"""
        async for session in get_session():
            try:
                await status_update_service.update_completed_pods_to_closed(session)
                await reminder_service.send_review_reminders(session)
                await reminder_service.send_deadline_reminders(session)
            finally:
                await session.close()

    # 시간별 작업 (1시간마다)
    async def hourly_tasks() -> None:
        """시간별 작업: 마감 알림"""
        async for session in get_session():
            try:
                await reminder_service.send_deadline_reminders(session)
            finally:
                await session.close()

    # 빈번한 작업 (5분마다)
    async def frequent_tasks() -> None:
        """빈번한 작업: 상태 업데이트 + 시작/취소 임박 알림"""
        async for session in get_session():
            try:
                await status_update_service.run_all_updates(session)
                await reminder_service.send_start_soon_reminders(session)
                await reminder_service.send_canceled_soon_reminders(session)
            finally:
                await session.close()

    # 스케줄러에 등록
    scheduler.register_daily_task(daily_tasks)
    scheduler.register_hourly_task(hourly_tasks)
    scheduler.register_frequent_task(frequent_tasks)

    logger.info("리마인더 작업이 스케줄러에 등록되었습니다")
