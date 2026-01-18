"""성향 테스트 점수 계산 서비스"""

from typing import Any, Dict, List


class TendencyCalculationService:
    """성향 테스트 점수 계산 로직을 처리하는 서비스"""

    # - MARK: 성향 테스트 점수 계산
    async def calculate_tendency_score(
        self, answers: Dict[int, int], survey_questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        성향 테스트 답변을 받아서 점수를 계산하고 결과를 반환

        Args:
            answers: {question_id: answer_id} 형태의 답변 딕셔너리
            survey_questions: 설문 질문 리스트

        Returns:
            {
                "tendency_type": "결과 타입",
                "total_score": 총점,
                "scores": {
                    "안방덕메": 점수,
                    "인싸덕메": 점수,
                    "올출덕메": 점수,
                    "순례덕메": 점수,
                    "서폿덕메": 점수,
                    "금손덕메": 점수
                },
                "answers": 원본 답변
            }
        """
        # 점수 초기화
        scores = {
            "안방덕메": 0,
            "인싸덕메": 0,
            "올출덕메": 0,
            "순례덕메": 0,
            "서폿덕메": 0,
            "금손덕메": 0,
        }

        # 각 답변에 대해 점수 계산
        for question_id, answer_id in answers.items():
            question = next(
                (q for q in survey_questions if q["id"] == question_id), None
            )
            if not question:
                continue

            answer = next(
                (a for a in question["answers"] if a["id"] == answer_id), None
            )
            if not answer:
                continue

            # 해당 덕메 타입에 점수 추가
            tendency_type = answer["tendencyType"]
            score = answer["score"]
            scores[tendency_type] += score

        # 총점 계산
        total_score = sum(scores.values())

        # 가장 높은 점수의 덕메 타입을 결과로 선택
        max_score = max(scores.values())
        result_types = [
            tendency_type
            for tendency_type, score in scores.items()
            if score == max_score
        ]

        # 결과 타입 매핑 (한글 -> 영문)
        type_mapping = {
            "안방덕메": "QUIET_MATE",
            "인싸덕메": "TOGETHER_MATE",
            "올출덕메": "FIELD_MATE",
            "순례덕메": "PILGRIM_MATE",
            "서폿덕메": "SUPPORT_MATE",
            "금손덕메": "CREATIVE_MATE",
        }

        # 결과 반환
        return {
            "tendency_type": type_mapping.get(result_types[0], "QUIET_MATE"),
            "total_score": total_score,
            "scores": scores,
            "answers": answers,
        }
