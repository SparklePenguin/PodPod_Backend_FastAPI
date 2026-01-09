"""Tendency Use Case - 비즈니스 로직 처리"""

from typing import List

from app.features.tendencies.exceptions import (
    TendencyResultNotFoundException,
    TendencySurveyNotFoundException,
)
from app.features.tendencies.repositories import TendencyRepository
from app.features.tendencies.schemas import (
    SubmitTendencyTestRequest,
    TendencyDto,
    TendencyResultDto,
    TendencySurveyDto,
    UserTendencyResultDto,
)
from app.features.tendencies.schemas.tendency_schemas import TendencyInfoDto
from app.features.tendencies.services.tendency_calculation_service import (
    TendencyCalculationService,
)
from app.features.users.models import User
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession


class TendencyUseCase:
    """성향 테스트 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        tendency_repo: TendencyRepository,
        calculation_service: TendencyCalculationService,
    ):
        self._session = session
        self._tendency_repo = tendency_repo
        self._calculation_service = calculation_service

    # - MARK: 성향 테스트 제출 및 결과 반환
    async def submit_tendency_test(
        self, user_id: int, request: SubmitTendencyTestRequest
    ) -> TendencyDto:
        """성향 테스트 제출 및 결과 반환"""
        # 설문 데이터 조회
        survey_data = await self.get_tendency_survey()

        # 답변을 딕셔너리 형태로 변환
        answers_dict = {answer.question_id: answer.id for answer in request.answers}

        # 점수 계산 (계산 서비스 사용)
        calculation_result = await self._calculation_service.calculate_tendency_score(
            answers_dict, survey_data.questions
        )

        # 결과 저장 (커밋 포함)
        await self.save_user_tendency_result(
            user_id, calculation_result["tendency_type"], answers_dict
        )

        # TendencyResult 조회
        tendency_result = await self.get_tendency_result(
            calculation_result["tendency_type"]
        )
        if not tendency_result:
            raise TendencyResultNotFoundException(calculation_result["tendency_type"])

        # TendencyDto 생성
        tendency_info_dict = getattr(tendency_result, "tendency_info", {})
        description = getattr(tendency_result, "description", "")

        return TendencyDto(
            type=calculation_result["tendency_type"],
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

    # - MARK: 모든 성향 테스트 결과 조회
    async def get_tendency_results(self) -> List[TendencyResultDto]:
        """모든 성향 테스트 결과 조회"""
        tendency_results = await self._tendency_repo.get_all_tendency_results()

        return [
            TendencyResultDto.model_validate(result, from_attributes=True)
            for result in tendency_results
        ]

    # - MARK: 특정 성향 테스트 결과 조회
    async def get_tendency_result(self, tendency_type: str) -> TendencyResultDto | None:
        """특정 성향 테스트 결과 조회"""
        tendency_result = await self._tendency_repo.get_tendency_result_by_type(
            tendency_type
        )

        if not tendency_result:
            return None

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

    # - MARK: 사용자 성향 테스트 결과 저장 (커밋 포함)
    async def save_user_tendency_result(
        self, user_id: int, tendency_type: str, answers: dict
    ) -> UserTendencyResultDto:
        """사용자의 성향 테스트 결과 저장 (기존 결과가 있으면 업데이트, 없으면 생성)"""
        existing_result = await self._tendency_repo.get_user_tendency_result(user_id)

        # User 테이블의 tendency_type 업데이트
        await self._session.execute(
            update(User).where(User.id == user_id).values(tendency_type=tendency_type)
        )

        if existing_result:
            # 기존 결과 업데이트
            await self._tendency_repo.update_user_tendency_result(
                user_id, tendency_type, answers
            )
            await self._session.commit()
            await self._session.refresh(existing_result)
            return UserTendencyResultDto.model_validate(
                existing_result, from_attributes=True
            )
        else:
            # 새 결과 생성
            new_result = await self._tendency_repo.create_user_tendency_result(
                user_id, tendency_type, answers
            )
            await self._session.commit()
            await self._session.refresh(new_result)
            return UserTendencyResultDto.model_validate(
                new_result, from_attributes=True
            )
