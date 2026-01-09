"""Pod DTO 변환 서비스

Pod 모델을 DTO로 변환하는 단일 책임을 가진 서비스입니다.
"""

import json
from datetime import date, datetime, time, timezone

from app.features.pods.models import Pod, PodStatus
from app.features.pods.schemas.pod_schemas import PodDetailDto, PodDto, PodImageDto


class PodDtoService:
    """Pod DTO 변환을 담당하는 서비스"""

    @staticmethod
    def parse_sub_categories(sub_categories: str | list | None) -> list[str]:
        """sub_categories 문자열을 리스트로 파싱"""
        if sub_categories is None:
            return []

        if isinstance(sub_categories, list):
            return sub_categories

        if isinstance(sub_categories, str):
            try:
                parsed = json.loads(sub_categories)
                if isinstance(parsed, list):
                    return parsed
                return []
            except (json.JSONDecodeError, TypeError):
                return []

        return []

    @staticmethod
    def normalize_status(status: PodStatus | str | None) -> PodStatus:
        """status를 PodStatus enum으로 정규화"""
        if status is None:
            return PodStatus.RECRUITING

        if isinstance(status, PodStatus):
            return status

        if isinstance(status, str):
            try:
                return PodStatus(status.upper())
            except ValueError:
                return PodStatus.RECRUITING

        return PodStatus.RECRUITING

    @staticmethod
    def convert_to_dto(pod: Pod) -> PodDto:
        """Pod 모델을 PodDto로 변환 (목록용, 간단한 정보)

        Args:
            pod: Pod 모델

        Returns:
            PodDto: 변환된 DTO
        """
        sub_categories = PodDtoService.parse_sub_categories(pod.sub_categories)
        status = PodDtoService.normalize_status(pod.status)

        # datetime 기본값 제공
        created_at = pod.created_at or datetime.now(timezone.utc)
        updated_at = pod.updated_at or datetime.now(timezone.utc)

        return PodDto(
            id=pod.id or 0,
            owner_id=pod.owner_id or 0,
            title=pod.title or "",
            thumbnail_url=pod.thumbnail_url or "",
            sub_categories=sub_categories,
            selected_artist_id=pod.selected_artist_id or 0,
            capacity=pod.capacity or 0,
            place=pod.place or "",
            meeting_date=pod.meeting_date if pod.meeting_date else date.today(),
            meeting_time=pod.meeting_time if pod.meeting_time else time.min,
            status=status,
            is_del=pod.is_del or False,
            chat_room_id=pod.chat_room_id or 0,
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def convert_to_detail_dto(pod: Pod) -> PodDetailDto:
        """Pod 모델을 PodDetailDto로 변환 (상세용)

        Args:
            pod: Pod 모델 (detail 관계 포함)

        Returns:
            PodDetailDto: 변환된 상세 DTO
        """
        sub_categories = PodDtoService.parse_sub_categories(pod.sub_categories)
        status = PodDtoService.normalize_status(pod.status)

        # datetime 기본값 제공
        created_at = pod.created_at or datetime.now(timezone.utc)
        updated_at = pod.updated_at or datetime.now(timezone.utc)

        # PodDetail 정보
        pod_detail = pod.detail if hasattr(pod, "detail") else None

        # 이미지 리스트 변환
        images_dto = []
        if hasattr(pod, "images") and pod.images:
            for img in sorted(pod.images, key=lambda x: x.display_order or 0):
                images_dto.append(PodImageDto.from_pod_image(img))

        return PodDetailDto(
            id=pod.id or 0,
            owner_id=pod.owner_id or 0,
            title=pod.title or "",
            description=pod_detail.description if pod_detail else "",
            image_url=pod_detail.image_url if pod_detail else None,
            thumbnail_url=pod.thumbnail_url,
            sub_categories=sub_categories,
            capacity=pod.capacity or 0,
            place=pod.place or "",
            address=pod_detail.address if pod_detail else "",
            sub_address=pod_detail.sub_address if pod_detail else None,
            x=pod_detail.x if pod_detail else None,
            y=pod_detail.y if pod_detail else None,
            meeting_date=pod.meeting_date if pod.meeting_date else date.today(),
            meeting_time=pod.meeting_time if pod.meeting_time else time.min,
            selected_artist_id=pod.selected_artist_id or 0,
            status=status,
            is_del=pod.is_del or False,
            chat_room_id=pod.chat_room_id or 0,
            images=images_dto,
            created_at=created_at,
            updated_at=updated_at,
            # 기본값 (이후 enrich에서 설정)
            is_liked=False,
            is_reviewed=False,
            applications=[],
            view_count=0,
            joined_users_count=0,
            like_count=0,
            joined_users=[],
            reviews=[],
        )

    @staticmethod
    def create_empty_dto() -> PodDto:
        """빈 PodDto 생성 (오류 시 기본값)"""
        return PodDto(
            id=0,
            owner_id=0,
            title="",
            thumbnail_url="",
            sub_categories=[],
            selected_artist_id=0,
            capacity=0,
            place="",
            meeting_date=date.today(),
            meeting_time=time.min,
            status=PodStatus.RECRUITING,
            is_del=False,
            chat_room_id=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
