"""Pod 카테고리 서비스

서브 카테고리 검증, 파싱, 변환을 담당하는 단일 책임 서비스입니다.
"""

import json
from typing import List

from app.features.pods.models.pod_models import (
    AccompanySubCategory,
    EtcSubCategory,
    GoodsSubCategory,
    TourSubCategory,
)


class PodCategoryService:
    """Pod 카테고리 검증 및 변환을 담당하는 서비스"""

    # 모든 유효한 카테고리 (클래스 로드 시 캐싱)
    _valid_categories: set[str] | None = None

    @classmethod
    def _get_valid_categories(cls) -> set[str]:
        """모든 유효한 카테고리 집합 반환 (캐싱)"""
        if cls._valid_categories is None:
            cls._valid_categories = set()
            cls._valid_categories.update([cat.name for cat in AccompanySubCategory])
            cls._valid_categories.update([cat.name for cat in GoodsSubCategory])
            cls._valid_categories.update([cat.name for cat in TourSubCategory])
            cls._valid_categories.update([cat.name for cat in EtcSubCategory])
        return cls._valid_categories

    @staticmethod
    def parse_to_list(sub_categories: str | list | None) -> list[str]:
        """sub_categories를 리스트로 파싱 (저장된 데이터 → 리스트)

        Args:
            sub_categories: JSON 문자열, 리스트, 또는 None

        Returns:
            파싱된 리스트 (빈 리스트 가능)
        """
        if sub_categories is None:
            return []

        if isinstance(sub_categories, list):
            return sub_categories

        if isinstance(sub_categories, str):
            try:
                parsed = json.loads(sub_categories)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError, ValueError):
                return []

        return []

    @staticmethod
    def parse_to_string(sub_categories: str | list | None) -> str | None:
        """sub_categories를 JSON 문자열로 변환 (입력 → 저장용)

        Args:
            sub_categories: 리스트, JSON 문자열, 또는 None

        Returns:
            JSON 문자열 또는 None (빈 리스트면 None)
        """
        if sub_categories is None:
            return None

        if isinstance(sub_categories, list):
            if not sub_categories:
                return None
            return json.dumps(sub_categories)

        if isinstance(sub_categories, str):
            try:
                parsed = json.loads(sub_categories)
                if not isinstance(parsed, list) or not parsed:
                    return None
                return sub_categories
            except (json.JSONDecodeError, ValueError):
                return None

        return None

    @classmethod
    def validate_and_filter(cls, categories: List[str]) -> List[str]:
        """서브 카테고리 검증 및 필터링

        유효하지 않은 카테고리는 필터링하고 경고를 출력합니다.

        Args:
            categories: 검증할 카테고리 리스트

        Returns:
            유효한 카테고리만 포함된 리스트
        """
        if not categories:
            return []

        valid_categories = cls._get_valid_categories()

        # 유효한 카테고리만 필터링
        valid_sub_categories = [cat for cat in categories if cat in valid_categories]

        # 유효하지 않은 카테고리 경고
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            cls._log_invalid_categories(invalid_categories)

        return valid_sub_categories

    @staticmethod
    def _log_invalid_categories(invalid_categories: List[str]) -> None:
        """유효하지 않은 카테고리 경고 출력"""
        goods_categories = [cat.name for cat in GoodsSubCategory]
        accompany_categories = [cat.name for cat in AccompanySubCategory]
        tour_categories = [cat.name for cat in TourSubCategory]
        etc_categories = [cat.name for cat in EtcSubCategory]

        print(
            f"""⚠️ 유효하지 않은 카테고리가 필터링되었습니다: {", ".join(invalid_categories)}

사용 가능한 카테고리:
📦 굿즈: {", ".join(goods_categories)}
👥 동행: {", ".join(accompany_categories)}
🗺️ 투어: {", ".join(tour_categories)}
📋 기타: {", ".join(etc_categories)}"""
        )

    @classmethod
    def is_valid(cls, category: str) -> bool:
        """단일 카테고리가 유효한지 확인"""
        return category in cls._get_valid_categories()

    @classmethod
    def validate_required(cls, sub_categories: str | list | None) -> list[str]:
        """필수 카테고리 검증 (빈 값이면 ValueError)

        Args:
            sub_categories: 검증할 카테고리

        Returns:
            파싱된 카테고리 리스트

        Raises:
            ValueError: 카테고리가 비어있거나 None인 경우
        """
        categories = cls.parse_to_list(sub_categories)
        if not categories:
            raise ValueError("서브 카테고리는 필수입니다")
        return categories
