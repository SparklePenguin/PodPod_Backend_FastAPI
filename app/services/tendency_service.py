import json
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tendency import TendencyResult, TendencySurvey, UserTendencyResult
from app.schemas.tendency import (
    TendencyResultDto,
    TendencySurveyDto,
    UserTendencyResultDto,
    Tendency,
    TendencyInfo,
)


class TendencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # - MARK: Flutter용 성향 테스트 점수 계산
    async def calculate_tendency_score_flutter(
        self, answers: List[Dict[str, int]]
    ) -> Tendency:
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
            raise Exception("성향 테스트 결과를 찾을 수 없습니다")

        # Tendency 객체 생성
        return Tendency(
            type=calculation_result["tendency_type"],  # 이미 대문자 스네이크 케이스
            description=tendency_result.description,
            tendency_info=TendencyInfo(
                main_type=tendency_result.tendency_info["mainType"],
                sub_type=tendency_result.tendency_info["subType"],
                speech_bubbles=tendency_result.tendency_info["speechBubbles"],
                one_line_descriptions=tendency_result.tendency_info[
                    "oneLineDescriptions"
                ],
                detailed_description=tendency_result.tendency_info[
                    "detailedDescription"
                ],
                keywords=tendency_result.tendency_info["keywords"],
            ),
        )

    # - MARK: 성향 테스트 점수 계산
    async def calculate_tendency_score(self, answers: Dict[int, int]) -> Dict[str, any]:
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
                (q for q in survey_data.questions if q["id"] == question_id),
                None,
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

    # - MARK: 성향 테스트 결과 조회
    async def get_tendency_results(self) -> List[TendencyResultDto]:
        """모든 성향 테스트 결과 조회"""
        from sqlalchemy import select

        result = await self.db.execute(select(TendencyResult))
        tendency_results = result.scalars().all()

        return [
            TendencyResultDto.model_validate(result, from_attributes=True)
            for result in tendency_results
        ]

    async def get_tendency_result(
        self, tendency_type: str
    ) -> Optional[TendencyResultDto]:
        """특정 성향 테스트 결과 조회"""
        from sqlalchemy import select

        # DB의 타입이 모두 대문자 언더스코어 형식으로 통일됨
        # 매핑 없이 직접 사용 (모든 타입이 UPPER_CASE 형식)
        mapped_type = tendency_type

        result = await self.db.execute(
            select(TendencyResult).where(TendencyResult.type == mapped_type)
        )
        tendency_result = result.scalar_one_or_none()

        if not tendency_result:
            return None

        return TendencyResultDto.model_validate(tendency_result, from_attributes=True)

    # - MARK: 성향 테스트 설문 조회
    async def get_tendency_survey(self) -> Optional[TendencySurveyDto]:
        """성향 테스트 설문 조회"""
        from sqlalchemy import select

        result = await self.db.execute(select(TendencySurvey))
        survey = result.scalar_one_or_none()

        if not survey:
            return None

        return TendencySurveyDto.model_validate(survey, from_attributes=True)

    # - MARK: 사용자 성향 테스트 결과 조회
    async def get_user_tendency_result(
        self, user_id: int
    ) -> Optional[UserTendencyResultDto]:
        """사용자의 성향 테스트 결과 조회"""
        from sqlalchemy import select

        result = await self.db.execute(
            select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
        )
        user_result = result.scalar_one_or_none()

        if not user_result:
            return None

        return UserTendencyResultDto.model_validate(user_result, from_attributes=True)

    # - MARK: 사용자 성향 테스트 결과 저장
    async def save_user_tendency_result(
        self, user_id: int, tendency_type: str, answers: dict
    ) -> None:
        """사용자의 성향 테스트 결과 저장"""
        # 기존 결과가 있으면 업데이트, 없으면 새로 생성
        existing_result = await self.get_user_tendency_result(user_id)

        if existing_result:
            # 기존 결과 업데이트
            from sqlalchemy import update

            await self.db.execute(
                update(UserTendencyResult)
                .where(UserTendencyResult.user_id == user_id)
                .values(tendency_type=tendency_type, answers=answers)
            )
        else:
            # 새 결과 생성
            new_result = UserTendencyResult(
                user_id=user_id, tendency_type=tendency_type, answers=answers
            )
            self.db.add(new_result)

        await self.db.commit()

    # - MARK: (내부용) MVP 성향 테스트 데이터 생성
    async def create_mvp_tendency_data(self) -> dict:
        """MVP 성향 테스트 데이터 생성 (내부용)"""
        try:
            # 성향 테스트 결과 데이터 로드
            with open("mvp_tend_test_result.json", "r", encoding="utf-8") as f:
                tendency_results = json.load(f)

            # 성향 테스트 설문 데이터 로드
            with open("mvp_tend_test_survey.json", "r", encoding="utf-8") as f:
                survey_data = json.load(f)

            # 기존 데이터 삭제
            from sqlalchemy import text

            await self.db.execute(text("DELETE FROM tendency_results"))
            await self.db.execute(text("DELETE FROM tendency_surveys"))

            # 성향 테스트 결과 삽입
            for result in tendency_results:
                new_result = TendencyResult(
                    type=result["type"],
                    description=result["description"],
                    tendency_info=result["tendencyInfo"],
                )
                self.db.add(new_result)

            # 성향 테스트 설문 삽입
            new_survey = TendencySurvey(
                title=survey_data["title"], survey_data=survey_data
            )
            self.db.add(new_survey)

            await self.db.commit()

            return {
                "tendency_results_count": len(tendency_results),
                "survey_created": True,
            }

        except Exception as e:
            await self.db.rollback()
            raise Exception(f"MVP 성향 테스트 데이터 생성 실패: {str(e)}")
