from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import UserCRUD
from app.crud.artist import ArtistCRUD
from app.schemas.common import ErrorResponse
from app.schemas.user import UpdateProfileRequest, UserDto, UserDtoInternal
from app.schemas.auth import SignUpRequest
from app.schemas.artist import ArtistDto
from app.core.security import get_password_hash
from typing import List, Optional


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_crud = UserCRUD(db)
        self.artist_crud = ArtistCRUD(db)

    # - MARK: 사용자 생성
    async def create_user(self, user_data: SignUpRequest) -> UserDto:
        # 이메일 중복 확인 (provider도 함께 확인)
        existing_user = await self.user_crud.get_by_email(user_data.email)
        if existing_user:
            # 같은 provider인지 확인
            if (
                user_data.auth_provider
                and existing_user.auth_provider == user_data.auth_provider
            ):
                # 같은 provider의 같은 계정이면 중복 에러
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error_code="email_already_exists",
                        status=status.HTTP_400_BAD_REQUEST,
                        message="이미 등록된 계정입니다",
                    ).model_dump(),
                )
            elif not user_data.auth_provider:
                # OAuth가 없는 경우(일반 회원가입)에는 이메일 중복 에러
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error_code="email_already_exists",
                        status=status.HTTP_400_BAD_REQUEST,
                        message="이메일이 이미 등록되어 있습니다",
                    ).model_dump(),
                )
            else:
                # 다른 OAuth provider인 경우 계속 진행 (새 계정 생성)
                pass

        # 비밀번호 해싱
        if user_data.password is not None:
            hashed_password = get_password_hash(user_data.password)
        else:
            hashed_password = None  # 소셜 로그인의 경우

        # 사용자 생성
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password

        user = await self.user_crud.create(user_dict)

        return UserDto.model_validate(user, from_attributes=True)

    # - MARK: (내부용) 사용자 목록 조회
    async def get_users(self) -> List[UserDtoInternal]:
        users = await self.user_crud.get_all()
        return [
            UserDtoInternal.model_validate(user, from_attributes=True) for user in users
        ]

    # - MARK: 사용자 조회
    async def get_user(self, user_id: int) -> UserDto:
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="user_not_found",
                    status=status.HTTP_404_NOT_FOUND,
                    message="사용자를 찾을 수 없습니다",
                ).model_dump(),
            )

        return UserDto.model_validate(user, from_attributes=True)

    # - MARK: (내부용) 사용자 조회 (모든 정보 포함)
    async def get_user_internal(self, user_id: int) -> UserDtoInternal:
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="user_not_found",
                    status=status.HTTP_404_NOT_FOUND,
                    message="사용자를 찾을 수 없습니다",
                ).model_dump(),
            )

        return UserDtoInternal.model_validate(user, from_attributes=True)

    # - MARK: (내부용) auth_provider와 auth_provider_id로 사용자 찾기
    async def get_user_by_auth_provider_id(
        self, auth_provider: str, auth_provider_id: str
    ) -> Optional[UserDto]:
        """auth_provider와 auth_provider_id로 사용자 찾기"""
        user = await self.user_crud.get_by_auth_provider_id(
            auth_provider, auth_provider_id
        )
        if not user:
            return None
        return UserDto.model_validate(user, from_attributes=True)

    # - MARK: 프로필 업데이트
    async def update_profile(
        self, user_id: int, user_data: UpdateProfileRequest
    ) -> UserDto:
        update_data = user_data.model_dump(exclude_unset=True)

        user = await self.user_crud.update_profile(user_id, update_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="user_not_found",
                    status=status.HTTP_404_NOT_FOUND,
                    message="사용자를 찾을 수 없습니다",
                ).model_dump(),
            )
        return UserDto.model_validate(user, from_attributes=True)

    # - MARK: 선호 아티스트 조회
    async def get_preferred_artists(self, user_id: int) -> List[ArtistDto]:
        """사용자의 선호 아티스트 목록 조회"""
        # 아티스트 ID 목록 가져오기
        artist_ids = await self.user_crud.get_preferred_artist_ids(user_id)

        # 각 아티스트 정보 가져오기
        artists = []
        for artist_id in artist_ids:
            artist = await self.artist_crud.get_by_id(artist_id)
            if artist:
                artists.append(ArtistDto(artist=artist))

        return artists

    # - MARK: 선호 아티스트 업데이트 (추가/제거)
    async def update_preferred_artists(
        self, user_id: int, artist_ids: List[int]
    ) -> List[ArtistDto]:
        """선호 아티스트 목록을 완전히 교체하여 업데이트"""
        # 아티스트 존재 확인
        for artist_id in artist_ids:
            artist = await self.artist_crud.get_by_id(artist_id)
            if not artist:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        error_code="artist_not_found",
                        status=status.HTTP_404_NOT_FOUND,
                        message=f"아티스트 ID {artist_id}를 찾을 수 없습니다",
                    ).model_dump(),
                )

        # 기존 선호 아티스트 모두 제거
        current_artist_ids = await self.user_crud.get_preferred_artist_ids(user_id)
        for current_artist_id in current_artist_ids:
            await self.user_crud.remove_preferred_artist(user_id, current_artist_id)

        # 새로운 선호 아티스트 추가
        for artist_id in artist_ids:
            await self.user_crud.add_preferred_artist(user_id, artist_id)

        # 업데이트된 선호 아티스트 목록 반환
        return await self.get_preferred_artists(user_id)
