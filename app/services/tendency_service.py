import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tendency import TendencyResult, TendencySurvey, UserTendencyResult
from app.schemas.tendency import (
    TendencyResultDto,
    TendencySurveyDto,
    UserTendencyResultDto,
)


class TendencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

        result = await self.db.execute(
            select(TendencyResult).where(TendencyResult.type == tendency_type)
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

        return TendencySurveyDto.from_orm(survey)

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
    ) -> UserTendencyResultDto:
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
        await self.db.refresh(new_result if not existing_result else existing_result)

        return await self.get_user_tendency_result(user_id)

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
