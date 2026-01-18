"""Pod Validation Service - 파티 검증 로직

파티 생성/수정 시 필수 필드 검증을 담당합니다.
"""

from app.features.pods.schemas import PodForm
from app.features.pods.services.pod_category_service import PodCategoryService


class PodValidationService:
    """파티 검증 서비스"""

    @staticmethod
    def validate_for_create(pod_form: PodForm) -> None:
        """파티 생성 시 필수 필드 검증

        Args:
            pod_form: 파티 생성 폼 데이터

        Raises:
            ValueError: 필수 필드가 누락된 경우
        """
        required_fields = {
            "title": pod_form.title,
            "sub_categories": pod_form.sub_categories,
            "capacity": pod_form.capacity,
            "place": pod_form.place,
            "address": pod_form.address,
            "meeting_date": pod_form.meeting_date,
            "selected_artist_id": pod_form.selected_artist_id,
        }

        missing_fields = [
            field for field, value in required_fields.items() if value is None
        ]

        if missing_fields:
            raise ValueError(f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}")

        # sub_categories 필수 검증 (PodCategoryService 사용)
        PodCategoryService.validate_required(pod_form.sub_categories)

    @staticmethod
    def validate_for_update(pod_form: PodForm) -> None:
        """파티 수정 시 검증

        수정 시에는 모든 필드가 필수가 아니므로,
        제공된 필드만 검증합니다.

        Args:
            pod_form: 파티 수정 폼 데이터
        """
        # 수정 시에는 sub_categories가 제공된 경우에만 검증
        if pod_form.sub_categories is not None:
            PodCategoryService.validate_required(pod_form.sub_categories)
