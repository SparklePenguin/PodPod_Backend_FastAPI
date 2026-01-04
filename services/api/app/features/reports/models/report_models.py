from enum import Enum


class ReportReason(str, Enum):
    """신고 사유 열거형"""

    ABUSIVE_LANGUAGE = "ABUSIVE_LANGUAGE"  # 욕설, 비속어 사용
    INAPPROPRIATE_MEETING = "INAPPROPRIATE_MEETING"  # 조건을 제시하는 만남 유도
    FINANCIAL_FRAUD = "FINANCIAL_FRAUD"  # 금전 요구 또는 거래 시도
    SPAM = "SPAM"  # 스팸 또는 도배 메시지
    OFF_TOPIC = "OFF_TOPIC"  # 운영 목적 외 채팅 사용
    FALSE_INFORMATION = "FALSE_INFORMATION"  # 허위 정보 기재 (나이, 성별 등)
    HARASSMENT = "HARASSMENT"  # 만남 강요, 부담 주는 행동
    OTHER = "OTHER"  # 그 외 다른 문제

    @classmethod
    def get_description(cls, reason: "ReportReason") -> str:
        """신고 사유에 대한 설명 반환"""
        descriptions = {
            cls.ABUSIVE_LANGUAGE: "욕설, 비속어 사용 - 불쾌한 언어 또는 욕설이 포함되어 있어요",
            cls.INAPPROPRIATE_MEETING: "조건을 제시하는 만남 유도 - 불건전한 만남을 유도하는 메시지가 있어요",
            cls.FINANCIAL_FRAUD: "금전 요구 또는 거래 시도 - 돈을 요구하거나 거래를 제안하고 있어요",
            cls.SPAM: "스팸 또는 도배 메시지 - 반복적이거나 의미 없는 메시지가 계속 전송 해요",
            cls.OFF_TOPIC: "운영 목적 외 채팅 사용 - 파티 목적과 무관한 내용을 반복적으로 올리고 있어요",
            cls.FALSE_INFORMATION: "허위 정보 기재 (나이, 성별 등) - 자신에 대한 정보를 거짓으로 작성했어요",
            cls.HARASSMENT: "만남 강요, 부담 주는 행동 - 불편하거나 강압적인 만남을 요구하고 있어요",
            cls.OTHER: "그 외 다른 문제가 있어요",
        }
        return descriptions.get(reason, "")

    @classmethod
    def get_all_reasons(cls) -> list[dict]:
        """모든 신고 사유 목록 반환 (id, code, description)"""
        reasons = [
            cls.ABUSIVE_LANGUAGE,
            cls.INAPPROPRIATE_MEETING,
            cls.FINANCIAL_FRAUD,
            cls.SPAM,
            cls.OFF_TOPIC,
            cls.FALSE_INFORMATION,
            cls.HARASSMENT,
            cls.OTHER,
        ]
        return [
            {
                "id": idx + 1,
                "code": reason.value,
                "description": cls.get_description(reason),
            }
            for idx, reason in enumerate(reasons)
        ]

    @classmethod
    def from_id(cls, reason_id: int) -> "ReportReason":
        """ID로부터 ReportReason 반환"""
        id_to_reason = {
            1: cls.ABUSIVE_LANGUAGE,
            2: cls.INAPPROPRIATE_MEETING,
            3: cls.FINANCIAL_FRAUD,
            4: cls.SPAM,
            5: cls.OFF_TOPIC,
            6: cls.FALSE_INFORMATION,
            7: cls.HARASSMENT,
            8: cls.OTHER,
        }
        reason = id_to_reason.get(reason_id)
        if not reason:
            raise ValueError(f"Invalid report reason ID: {reason_id}")
        return reason
