"""Tendency DTO 변환 서비스

성향 관련 데이터를 DTO로 변환하는 단일 책임 서비스입니다.
"""

from typing import Any, Dict

from app.features.tendencies.schemas.tendency_schemas import TendencyInfoDto


class TendencyDtoService:
    """Tendency DTO 변환을 담당하는 서비스"""

    @staticmethod
    def convert_to_info_dto(tendency_info: Dict[str, Any] | None) -> TendencyInfoDto:
        """tendency_info dict를 TendencyInfoDto로 변환

        Args:
            tendency_info: 성향 정보 딕셔너리 (camelCase 키 사용)

        Returns:
            TendencyInfoDto: 변환된 DTO
        """
        if not tendency_info:
            return TendencyDtoService.create_empty_info_dto()

        return TendencyInfoDto(
            main_type=tendency_info.get("mainType", ""),
            sub_type=tendency_info.get("subType", ""),
            speech_bubbles=tendency_info.get("speechBubbles", []),
            one_line_descriptions=tendency_info.get("oneLineDescriptions", []),
            detailed_description=tendency_info.get("detailedDescription", ""),
            keywords=tendency_info.get("keywords", []),
        )

    @staticmethod
    def create_empty_info_dto() -> TendencyInfoDto:
        """빈 TendencyInfoDto 생성 (기본값)"""
        return TendencyInfoDto(
            main_type="",
            sub_type="",
            speech_bubbles=[],
            one_line_descriptions=[],
            detailed_description="",
            keywords=[],
        )
