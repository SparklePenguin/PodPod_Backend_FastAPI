"""
채팅 Pod 서비스
Pod 정보 조회 및 변환 담당
"""

import json
import logging
from datetime import datetime, time, timezone

from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.schemas import PodDto
from app.features.pods.services.pod_dto_service import PodDtoService

logger = logging.getLogger(__name__)


class ChatPodService:
    """채팅 Pod 서비스 - Pod 정보 조회 및 변환 담당"""

    def __init__(self, pod_repo: PodRepository) -> None:
        """
        Args:
            pod_repo: Pod 레포지토리
        """
        self._pod_repo = pod_repo

    # - MARK: Pod 정보 추출 (채널 메타데이터에서)
    @staticmethod
    def extract_pod_info_from_metadata(
        channel_metadata: dict | None, room_id: int
    ) -> tuple[int | None, str | None]:
        """채널 메타데이터에서 Pod ID와 제목 추출"""
        pod_id = None
        pod_title = None

        if channel_metadata:
            data = channel_metadata.get("data", {})
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    data = {}
            pod_id = data.get("id")
            pod_title = data.get("title")

        # room_id에서 pod_id 유추 가능 (ChatRoom.pod_id가 있으므로 메타데이터에서 가져오는 게 맞음)

        return pod_id, pod_title

    # - MARK: Pod 정보 조회 및 DTO 변환
    async def get_pod_info(self, pod_id: int) -> tuple[str | None, dict | None]:
        """Pod 정보 조회 및 PodDto로 변환"""
        try:
            pod = await self._pod_repo.get_pod_by_id(pod_id)
            if not pod:
                return None, None

            # PodDto 변환
            def _convert_to_timestamp(meeting_date, meeting_time) -> int:
                if meeting_date is None:
                    return 0
                if meeting_time is None:
                    dt = datetime.combine(meeting_date, time.min, tzinfo=timezone.utc)
                else:
                    dt = datetime.combine(
                        meeting_date, meeting_time, tzinfo=timezone.utc
                    )
                return int(dt.timestamp() * 1000)

            sub_categories = PodDtoService.parse_sub_categories(pod.sub_categories)

            simple_pod = PodDto(
                id=pod.id,
                owner_id=pod.owner_id,
                title=pod.title,
                thumbnail_url=pod.thumbnail_url or "",
                sub_categories=sub_categories,
                meeting_place=pod.place,
                meeting_date=_convert_to_timestamp(pod.meeting_date, pod.meeting_time),
            )
            simple_pod_dict = simple_pod.model_dump(mode="json", by_alias=True)

            return pod.title, simple_pod_dict

        except Exception as e:
            logger.error(f"Pod 정보 조회 실패: pod_id={pod_id}, error={e}")
            return None, None
