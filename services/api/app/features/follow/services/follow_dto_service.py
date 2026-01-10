"""팔로우 DTO 변환 서비스"""

from app.common.schemas import PageDto
from app.features.users.models import User
from app.features.users.schemas import UserDto


class FollowDtoService:
    """팔로우 관련 DTO 변환을 담당하는 서비스"""

    @staticmethod
    def create_user_dto(
        user: User,
        tendency_type: str | None = None,
        is_following: bool = False,
    ) -> UserDto:
        """User 모델을 UserDto로 변환"""
        if user.id is None or not isinstance(user.id, int):
            raise ValueError("User ID가 유효하지 않습니다.")

        return UserDto(
            id=user.id,
            nickname=user.nickname or "",
            profile_image=user.profile_image or "",
            intro=user.intro or "",
            tendency_type=tendency_type or "",
            is_following=is_following,
        )

    @staticmethod
    def create_page_dto(
        items: list,
        page: int,
        size: int,
        total_count: int,
    ) -> PageDto:
        """PageDto 생성"""
        return PageDto.create(
            items=items,
            page=page,
            size=size,
            total_count=total_count,
        )
