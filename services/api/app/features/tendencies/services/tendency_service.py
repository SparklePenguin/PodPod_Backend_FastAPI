from typing import Any, Dict, List

from app.features.tendencies.exceptions import (
    TendencyResultNotFoundException,
    TendencySurveyNotFoundException,
)
from app.features.tendencies.repositories import TendencyRepository
from app.features.tendencies.schemas import (
    SubmitTendencyTestRequest,
    TendencyDto,
    TendencyInfoDto,
    TendencyResultDto,
    TendencySurveyDto,
    UserTendencyResultDto,
)
from sqlalchemy.ext.asyncio import AsyncSession


class TendencyService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tendency_repo = TendencyRepository(session)

    # - MARK: 성향 테스트 제출 및 결과 반환
    async def submit_tendency_test(
        self, user_id: int, request: SubmitTendencyTestRequest
    ) -> TendencyDto:
        """성향 테스트 제출 및 결과 반환"""
        # 답변을 딕셔너리 형태로 변환
        answers_dict = {answer.question_id: answer.id for answer in request.answers}

        # 점수 계산
        calculation_result = await self.calculate_tendency_score(answers_dict)

        # 결과 저장
        await self.save_user_tendency_result(
            user_id, calculation_result["tendency_type"], answers_dict
        )

        # Tendency 객체 생성
        return await self.calculate_tendency_score_flutter(
            [
                {"questionId": answer.question_id, "answerId": answer.id}
                for answer in request.answers
            ]
        )

    # - MARK: Flutter용 성향 테스트 점수 계산
    async def calculate_tendency_score_flutter(
        self, answers: List[Dict[str, int]]
    ) -> TendencyDto:
        """
        Flutter용 성향 테스트 답변을 받아서 점수를 계산하고 Tendency 객체를 반환

        Args:
            answers: [{"questionId": int, "answerId": int}] 형태의 답변 리스트

        Returns:
            Tendency 객체
        """
        # 답변을 딕셔너리 형태로 변환
        answers_dict = {answer["questionId"]: answer["answerId"] for answer in answers}

        # 기존 점수 계산 함수 사용
        calculation_result = await self.calculate_tendency_score(answers_dict)

        # TendencyResult 조회
        tendency_result = await self.get_tendency_result(
            calculation_result["tendency_type"]
        )
        if not tendency_result:
            raise TendencyResultNotFoundException(
                calculation_result.get("tendency_type")
            )

        # tendency_result가 None이 아님을 확인했으므로 안전하게 접근
        tendency_info_dict = getattr(tendency_result, "tendency_info", {})
        description = getattr(tendency_result, "description", "")

        # Tendency 객체 생성
        return TendencyDto(
            type=calculation_result["tendency_type"],  # 이미 대문자 스네이크 케이스
            description=description,
            tendency_info=TendencyInfoDto(
                main_type=tendency_info_dict.get("mainType", ""),
                sub_type=tendency_info_dict.get("subType", ""),
                speech_bubbles=tendency_info_dict.get("speechBubbles", []),
                one_line_descriptions=tendency_info_dict.get("oneLineDescriptions", []),
                detailed_description=tendency_info_dict.get("detailedDescription", ""),
                keywords=tendency_info_dict.get("keywords", []),
            ),
        )

    # - MARK: 성향 테스트 점수 계산
    async def calculate_tendency_score(self, answers: Dict[int, int]) -> Dict[str, Any]:
        """
        성향 테스트 답변을 받아서 점수를 계산하고 결과를 반환

        Args:
            answers: {question_id: answer_id} 형태의 답변 딕셔너리

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
        # 설문 데이터 로드
        survey_data = await self.get_tendency_survey()
        if not survey_data:
            raise Exception("설문 데이터를 찾을 수 없습니다")

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
                (q for q in survey_data.questions if q["id"] == question_id), None
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

    # - MARK: 모든 성향 테스트 결과 조회
    async def get_tendency_results(self) -> List[TendencyResultDto]:
        """모든 성향 테스트 결과 조회"""
        tendency_results = await self._tendency_repo.get_all_tendency_results()

        return [
            TendencyResultDto.model_validate(result, from_attributes=True)
            for result in tendency_results
        ]

    # - MARK: 특정 성향 테스트 결과 조회
    async def get_tendency_result(self, tendency_type: str) -> TendencyResultDto:
        """특정 성향 테스트 결과 조회"""
        tendency_result = await self._tendency_repo.get_tendency_result_by_type(
            tendency_type
        )

        if not tendency_result:
            raise TendencyResultNotFoundException(tendency_type)

        return TendencyResultDto.model_validate(tendency_result, from_attributes=True)

    # - MARK: 성향 테스트 설문 조회
    async def get_tendency_survey(self) -> TendencySurveyDto:
        """성향 테스트 설문 조회"""
        survey = await self._tendency_repo.get_tendency_survey()

        if not survey:
            raise TendencySurveyNotFoundException()

        return TendencySurveyDto.from_survey_data(survey)

    # - MARK: 사용자 성향 테스트 결과 조회
    async def get_user_tendency_result(
        self, user_id: int
    ) -> UserTendencyResultDto | None:
        """사용자의 성향 테스트 결과 조회"""
        user_result = await self._tendency_repo.get_user_tendency_result(user_id)

        if not user_result:
            return None

        return UserTendencyResultDto.model_validate(user_result, from_attributes=True)

    # - MARK: 사용자 성향 테스트 결과 저장
    async def save_user_tendency_result(
        self, user_id: int, tendency_type: str, answers: dict
    ) -> None:
        """사용자의 성향 테스트 결과 저장"""
        await self._tendency_repo.save_user_tendency_result(
            user_id, tendency_type, answers
        )
