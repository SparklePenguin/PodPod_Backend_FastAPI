"""스케줄러 인프라 - 주기적인 작업 실행 관리

순수 스케줄러 인프라만 담당합니다.
실제 작업은 콜백으로 등록하여 실행합니다.

사용 예시:
    from app.core.scheduler import Scheduler

    scheduler = Scheduler()
    scheduler.register_daily_task(my_daily_task)
    scheduler.register_frequent_task(my_5min_task)
    await scheduler.start()
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

# 타입 정의
TaskCallback = Callable[[], Awaitable[None]]


class SchedulerConfig:
    """스케줄러 설정"""

    DAILY_HOUR = 10  # 일일 스케줄러 실행 시간 (오전 10시)
    HOURLY_INTERVAL = 60 * 60  # 1시간 (초)
    FIVE_MIN_INTERVAL = 5 * 60  # 5분 (초)

    # 에러 발생 시 재시도 간격
    DAILY_RETRY_INTERVAL = 60 * 60  # 1시간
    HOURLY_RETRY_INTERVAL = 10 * 60  # 10분
    FIVE_MIN_RETRY_INTERVAL = 2 * 60  # 2분


class Scheduler:
    """스케줄러 - 주기적인 작업 실행 관리

    콜백 방식으로 작업을 등록하고 주기적으로 실행합니다.
    """

    def __init__(self, config: SchedulerConfig | None = None):
        self.config = config or SchedulerConfig()
        self._daily_tasks: list[TaskCallback] = []
        self._hourly_tasks: list[TaskCallback] = []
        self._frequent_tasks: list[TaskCallback] = []

    def register_daily_task(self, task: TaskCallback) -> None:
        """일일 작업 등록 (매일 오전 10시)"""
        self._daily_tasks.append(task)
        logger.debug(f"일일 작업 등록: {task.__name__}")

    def register_hourly_task(self, task: TaskCallback) -> None:
        """시간별 작업 등록 (1시간마다)"""
        self._hourly_tasks.append(task)
        logger.debug(f"시간별 작업 등록: {task.__name__}")

    def register_frequent_task(self, task: TaskCallback) -> None:
        """빈번한 작업 등록 (5분마다)"""
        self._frequent_tasks.append(task)
        logger.debug(f"5분 작업 등록: {task.__name__}")

    async def start(self) -> None:
        """스케줄러 시작"""
        logger.info("스케줄러 시작:")
        logger.info(f"- 매일 오전 {self.config.DAILY_HOUR}시: {len(self._daily_tasks)}개 작업")
        logger.info(f"- 5분마다: {len(self._frequent_tasks)}개 작업")
        logger.info(f"- 1시간마다: {len(self._hourly_tasks)}개 작업")

        await asyncio.gather(
            self._run_daily_loop(),
            self._run_frequent_loop(),
            self._run_hourly_loop(),
        )

    # ==================== 스케줄러 루프 ====================

    async def _run_daily_loop(self) -> None:
        """매일 지정된 시간에 실행되는 루프"""
        while True:
            try:
                await self._wait_until_hour(self.config.DAILY_HOUR)

                logger.info("일일 스케줄러 실행 시작")
                await self._execute_tasks(self._daily_tasks)
                logger.info("일일 스케줄러 실행 완료")

            except Exception as e:
                logger.error(f"일일 스케줄러 실행 중 오류: {e}")
                await asyncio.sleep(self.config.DAILY_RETRY_INTERVAL)

    async def _run_hourly_loop(self) -> None:
        """1시간마다 실행되는 루프"""
        while True:
            try:
                logger.info("시간별 스케줄러 실행 시작")
                await self._execute_tasks(self._hourly_tasks)
                logger.info("시간별 스케줄러 실행 완료")

                await asyncio.sleep(self.config.HOURLY_INTERVAL)

            except Exception as e:
                logger.error(f"시간별 스케줄러 실행 중 오류: {e}")
                await asyncio.sleep(self.config.HOURLY_RETRY_INTERVAL)

    async def _run_frequent_loop(self) -> None:
        """5분마다 실행되는 루프"""
        while True:
            try:
                logger.info("5분 스케줄러 실행 시작")
                await self._execute_tasks(self._frequent_tasks)
                logger.info("5분 스케줄러 실행 완료")

                await asyncio.sleep(self.config.FIVE_MIN_INTERVAL)

            except Exception as e:
                logger.error(f"5분 스케줄러 실행 중 오류: {e}")
                await asyncio.sleep(self.config.FIVE_MIN_RETRY_INTERVAL)

    # ==================== 유틸리티 ====================

    async def _execute_tasks(self, tasks: list[TaskCallback]) -> None:
        """등록된 작업들 순차 실행"""
        for task in tasks:
            try:
                await task()
            except Exception as e:
                logger.error(f"작업 실행 중 오류 ({task.__name__}): {e}")

    async def _wait_until_hour(self, target_hour: int) -> None:
        """지정된 시간까지 대기"""
        now = datetime.now(timezone.utc)
        target_time = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)

        if now >= target_time:
            target_time = target_time + timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()

        logger.info(f"다음 스케줄러 실행까지 {wait_seconds / 3600:.1f}시간 대기")
        await asyncio.sleep(wait_seconds)


# 전역 스케줄러 인스턴스
_scheduler: Scheduler | None = None


def get_scheduler() -> Scheduler:
    """스케줄러 인스턴스 반환 (싱글톤)"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


async def start_scheduler() -> None:
    """스케줄러 시작 (하위 호환성)"""
    scheduler = get_scheduler()
    await scheduler.start()
