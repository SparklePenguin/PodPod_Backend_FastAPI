from app.features.follow.models import Follow
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class FollowRepository:
    """팔로우 기본 CRUD Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 팔로우 생성
    async def create_follow(self, follower_id: int, following_id: int) -> Follow | None:
        """팔로우 생성"""
        try:
            # 자기 자신을 팔로우하는지 확인
            if follower_id == following_id:
                return None

            # 기존 팔로우 레코드 확인 (활성화 상태 무관)
            existing_follow = await self.get_follow_any_status(
                follower_id, following_id
            )
            if existing_follow:
                is_active_value = getattr(existing_follow, "is_active", False)
                if is_active_value:
                    return existing_follow
                else:
                    # 비활성화된 팔로우가 있으면 재활성화
                    setattr(existing_follow, "is_active", True)
                    await self._session.commit()
                    return existing_follow

            # 새로운 팔로우 생성
            follow = Follow(follower_id=follower_id, following_id=following_id)
            self._session.add(follow)
            await self._session.commit()
            await self._session.refresh(follow)
            return follow
        except Exception:
            await self._session.rollback()
            return None

    # - MARK: 팔로우 취소
    async def delete_follow(self, follower_id: int, following_id: int) -> bool:
        """팔로우 취소 (알림 설정은 보존)"""
        try:
            follow = await self.get_follow_any_status(follower_id, following_id)
            if not follow:
                return False

            # 레코드 삭제 대신 is_active = False로 업데이트
            setattr(follow, "is_active", False)
            await self._session.commit()
            return True
        except Exception:
            await self._session.rollback()
            return False

    # - MARK: 특정 팔로우 조회 (활성화된 것만)
    async def get_follow(self, follower_id: int, following_id: int) -> Follow | None:
        """특정 팔로우 조회 (활성화된 것만)"""
        query = select(Follow).where(
            and_(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
                Follow.is_active,
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    # - MARK: 특정 팔로우 조회 (활성화 상태 무관)
    async def get_follow_any_status(
        self, follower_id: int, following_id: int
    ) -> Follow | None:
        """특정 팔로우 조회 (활성화 상태 무관)"""
        query = select(Follow).where(
            and_(Follow.follower_id == follower_id, Follow.following_id == following_id)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    # - MARK: 팔로우 관계 존재 여부 확인
    async def check_follow_exists(self, follower_id: int, following_id: int) -> bool:
        """팔로우 관계 존재 여부 확인"""
        query = select(Follow).where(
            and_(Follow.follower_id == follower_id, Follow.following_id == following_id)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none() is not None

    # - MARK: 사용자 관련 모든 팔로우 관계 삭제
    async def delete_all_by_user(self, user_id: int) -> None:
        """특정 사용자와 관련된 모든 팔로우 관계 삭제"""
        # 해당 사용자가 팔로워인 경우와 팔로잉인 경우 모두 삭제
        await self._session.execute(
            delete(Follow).where(
                or_(Follow.follower_id == user_id, Follow.following_id == user_id)
            )
        )
        await self._session.commit()
