"""상태 업데이트 서비스 - 스케줄러에서 호출되는 상태 변경 로직"""

import logging
from datetime import date, datetime, timezone

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.pods.models import Pod, PodStatus

logger = logging.getLogger(__name__)


class StatusUpdateService:
    """상태 업데이트 서비스

    스케줄러에서 호출되어 파티 상태를 자동으로 변경합니다.
    - COMPLETED → CLOSED (미팅일 다음날)
    - RECRUITING → CANCELED (미팅 시간 지남)
    """

    async def update_completed_pods_to_closed(self, session: AsyncSession):
        """확정(COMPLETED) 파티를 종료(CLOSED)로 변경

        미팅일이 지난 확정 파티를 종료 상태로 변경합니다.
        """
        try:
            today = date.today()

            # 미팅일이 오늘보다 이전인 COMPLETED 파티 조회
            query = select(Pod).where(
                and_(
                    Pod.meeting_date < today,
                    func.upper(Pod.status) == PodStatus.COMPLETED.value.upper(),
                )
            )

            result = await session.execute(query)
            completed_pods = result.scalars().all()

            if not completed_pods:
                return

            logger.info(f"종료 처리 대상 파티: {len(completed_pods)}개")

            # 각 파티 상태 변경
            for pod in completed_pods:
                try:
                    pod_id = getattr(pod, "id", None)
                    if pod_id is None:
                        continue

                    stmt = (
                        update(Pod)
                        .where(Pod.id == pod_id)
                        .values(status=PodStatus.CLOSED.value)
                    )
                    await session.execute(stmt)

                    logger.info(
                        f"파티 상태 변경: pod_id={pod_id}, "
                        f"title={pod.title}, COMPLETED → CLOSED"
                    )

                except Exception as e:
                    logger.error(f"파티 상태 변경 실패: pod_id={pod.id}, error={e}")

            await session.commit()
            logger.info(f"파티 종료 처리 완료: {len(completed_pods)}개")

        except Exception as e:
            logger.error(f"파티 종료 처리 중 오류: {e}")
            await session.rollback()

    async def cancel_unconfirmed_pods(self, session: AsyncSession):
        """미확정 파티 취소 처리

        미팅 시간이 지난 모집 중(RECRUITING) 파티를 취소(CANCELED)로 변경합니다.
        """
        try:
            now = datetime.now(timezone.utc)

            # 모집 중인 모든 파티 조회
            query = select(Pod).where(
                func.upper(Pod.status) == PodStatus.RECRUITING.value.upper()
            )

            result = await session.execute(query)
            recruiting_pods = result.scalars().all()

            # 미팅 시간이 지난 파티 필터링
            unconfirmed_pods = []
            for pod in recruiting_pods:
                meeting_date = getattr(pod, "meeting_date", None)
                meeting_time = getattr(pod, "meeting_time", None)
                if meeting_date is None or meeting_time is None:
                    continue

                meeting_datetime = datetime.combine(
                    meeting_date, meeting_time, tzinfo=timezone.utc
                )

                # 미팅 시간이 지났으면 취소 대상
                if meeting_datetime <= now:
                    unconfirmed_pods.append(pod)

            if not unconfirmed_pods:
                return

            logger.info(f"취소 처리 대상 파티: {len(unconfirmed_pods)}개")

            # 각 파티 취소 처리
            for pod in unconfirmed_pods:
                try:
                    pod_status_value = (
                        pod.status.value.upper()
                        if hasattr(pod.status, "value")
                        else str(pod.status).upper()
                    )

                    if pod_status_value != PodStatus.RECRUITING.value.upper():
                        logger.warning(
                            f"파티 상태가 RECRUITING이 아님: pod_id={pod.id}, "
                            f"status={pod_status_value}"
                        )
                        continue

                    # 상태 변경 및 소프트 삭제
                    pod.status = PodStatus.CANCELED
                    pod.is_del = True

                    logger.info(
                        f"파티 취소 처리: pod_id={pod.id}, title={pod.title}, "
                        f"meeting_date={pod.meeting_date}, "
                        f"meeting_time={pod.meeting_time}"
                    )

                except Exception as e:
                    logger.error(f"파티 취소 처리 실패: pod_id={pod.id}, error={e}")

            await session.commit()
            logger.info(f"파티 취소 처리 완료: {len(unconfirmed_pods)}개")

        except Exception as e:
            logger.error(f"파티 취소 처리 중 오류: {e}")
            await session.rollback()

    async def run_all_updates(self, db: AsyncSession):
        """모든 상태 업데이트 실행

        스케줄러에서 한 번에 호출할 수 있는 통합 메서드입니다.
        """
        await self.update_completed_pods_to_closed(db)
        await self.cancel_unconfirmed_pods(db)
