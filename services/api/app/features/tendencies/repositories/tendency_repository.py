from typing import List

from app.features.tendencies.models import (
    TendencyResult,
    TendencySurvey,
    UserTendencyResult,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class TendencyRepository:
    """성향 테스트 관련 데이터베이스 작업"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 모든 성향 테스트 결과 조회
    async def get_all_tendency_results(self) -> List[TendencyResult]:
        """모든 성향 테스트 결과 조회"""
        result = await self._session.execute(select(TendencyResult))
        return list(result.scalars().all())

    # - MARK: 성향 타입으로 결과 조회
    async def get_tendency_result_by_type(
        self, tendency_type: str
    ) -> TendencyResult | None:
        """특정 성향 타입의 결과 조회"""
        result = await self._session.execute(
            select(TendencyResult).where(TendencyResult.type == tendency_type)
        )
        return result.scalar_one_or_none()

    # - MARK: 성향 테스트 설문 조회
    async def get_tendency_survey(self) -> TendencySurvey | None:
        """성향 테스트 설문 조회"""
        result = await self._session.execute(select(TendencySurvey))
        return result.scalar_one_or_none()

    # - MARK: 사용자 성향 결과 조회
    async def get_user_tendency_result(self, user_id: int) -> UserTendencyResult | None:
        """사용자의 성향 테스트 결과 조회"""
        result = await self._session.execute(
            select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
        )
        return result.scalar_one_or_none()

    # - MARK: 사용자 성향 결과 저장
    async def save_user_tendency_result(
        self, user_id: int, tendency_type: str, answers: dict
    ) -> UserTendencyResult:
        """사용자의 성향 테스트 결과 저장 (기존 결과가 있으면 업데이트, 없으면 생성)"""
        existing_result = await self.get_user_tendency_result(user_id)

        if existing_result:
            # 기존 결과 업데이트
            await self._session.execute(
                update(UserTendencyResult)
                .where(UserTendencyResult.user_id == user_id)
                .values(tendency_type=tendency_type, answers=answers)
            )
            await self._session.commit()
            await self._session.refresh(existing_result)
            return existing_result
        else:
            # 새 결과 생성
            new_result = UserTendencyResult(
                user_id=user_id, tendency_type=tendency_type, answers=answers
            )
            self._session.add(new_result)
            await self._session.commit()
            await self._session.refresh(new_result)
            return new_result
