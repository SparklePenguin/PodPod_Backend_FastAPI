"""Block User Use Case - 사용자 차단 관련 비즈니스 로직 처리"""

from datetime import datetime, timezone

from app.common.schemas import PageDto
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.tendencies.repositories.tendency_repository import TendencyRepository
from app.features.users.exceptions import (
    BlockNotFoundException,
    CannotBlockSelfException,
    UserNotFoundException,
)
from app.features.users.repositories import BlockUserRepository, UserRepository
from app.features.users.schemas import BlockInfoDto, UserDto
from app.features.users.services.user_dto_service import UserDtoService
from sqlalchemy.ext.asyncio import AsyncSession


class BlockUserUseCase:
    """사용자 차단 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        block_repo: BlockUserRepository,
        user_repo: UserRepository,
        follow_repo: FollowRepository,
        tendency_repo: TendencyRepository,
    ):
        self._session = session
        self._block_repo = block_repo
        self._user_repo = user_repo
        self._follow_repo = follow_repo
        self._tendency_repo = tendency_repo

    # - MARK: 사용자 차단
    async def block_user(self, blocker_id: int, blocked_id: int) -> BlockInfoDto:
        """사용자 차단 (팔로우 관계도 함께 삭제)"""
        # 자기 자신을 차단하려는 경우
        if blocker_id == blocked_id:
            raise CannotBlockSelfException()

        # 차단할 사용자 존재 확인
        blocked_user = await self._user_repo.get_by_id(blocked_id)
        if not blocked_user:
            raise UserNotFoundException(blocked_id)

        # 차단 생성
        block = await self._block_repo.create_block(blocker_id, blocked_id)
        if not block:
            raise UserNotFoundException(blocked_id)

        # 팔로우 관계 삭제 (양방향 모두)
        # 1. 내가 차단한 사람을 팔로우하고 있었다면 팔로우 해제
        await self._follow_repo.delete_follow(blocker_id, blocked_id)

        # 2. 차단한 사람이 나를 팔로우하고 있었다면 팔로우 해제
        await self._follow_repo.delete_follow(blocked_id, blocker_id)

        # 트랜잭션 커밋
        await self._session.commit()
        if block:
            await self._session.refresh(block)

        # datetime 기본값 제공
        created_at_val = (
            block.created_at
            if block.created_at is not None
            else datetime.now(timezone.utc)
        )

        return BlockInfoDto(
            blocker_id=block.blocker_id,
            blocked_id=block.blocked_id,
            created_at=created_at_val,
        )

    # - MARK: 사용자 차단 해제
    async def unblock_user(self, blocker_id: int, blocked_id: int) -> None:
        """사용자 차단 해제"""
        success = await self._block_repo.delete_block(blocker_id, blocked_id)
        if not success:
            raise BlockNotFoundException()

        # 트랜잭션 커밋
        await self._session.commit()

    # - MARK: 차단한 사용자 목록 조회
    async def get_blocked_users(
        self, blocker_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserDto]:
        """차단한 사용자 목록 조회"""
        blocked_data, total_count = await self._block_repo.get_blocked_users(
            blocker_id, page, size
        )

        users = []
        for user, blocked_at in blocked_data:
            # 성향 타입 조회
            if user.id is None:
                continue
            try:
                user_tendency = await self._tendency_repo.get_user_tendency_result(
                    user.id
                )
                if user_tendency:
                    tendency_type_raw = user_tendency.tendency_type
                    tendency_type = (
                        str(tendency_type_raw)
                        if tendency_type_raw is not None
                        else None
                    )
                else:
                    tendency_type = None
            except Exception:
                tendency_type = None

            user_dto = UserDtoService.create_user_dto(
                user, tendency_type or "", is_following=False
            )
            users.append(user_dto)

        # PageDto 생성
        return PageDto.create(
            items=users,
            page=page,
            size=size,
            total_count=total_count,
        )
