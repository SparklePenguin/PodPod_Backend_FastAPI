from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import UserCRUD
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.auth import RegisterRequest
from app.core.security import get_password_hash
from typing import List, Optional, Dict, Any


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_crud = UserCRUD(db)

    async def create_user(self, user_data: RegisterRequest) -> UserResponse:
        # 이메일 중복 확인
        existing_user = await self.user_crud.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이메일이 이미 등록되어 있습니다",
            )

        # 비밀번호 해싱
        hashed_password = get_password_hash(user_data.password)

        # 사용자 생성
        user_dict = user_data.dict(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        user_dict["auth_provider"] = "email"

        user = await self.user_crud.create(user_dict)

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            profile_image=user.profile_image,
            auth_provider=user.auth_provider,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def get_users(self) -> List[UserResponse]:
        users = await self.user_crud.get_all()
        return [
            UserResponse(
                id=user[0],
                email=user[2],
                username=user[1],
                full_name=user[4],
                profile_image=user[5],
                auth_provider=user[11],
                is_active=user[6],
                created_at=user[8],
            )
            for user in users
        ]

    async def get_user(self, user_id: int) -> UserResponse:
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다",
            )

        return UserResponse(
            id=user[0],
            email=user[2],
            username=user[1],
            full_name=user[4],
            profile_image=user[5],
            auth_provider=user[11],
            is_active=user[6],
            created_at=user[8],
        )

    async def update_user(
        self, user_id: int, user_data: Dict[str, Any]
    ) -> UserResponse:
        user = await self.user_crud.update(user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다",
            )

        return UserResponse(
            id=user[0],
            email=user[2],
            username=user[1],
            full_name=user[4],
            profile_image=user[5],
            auth_provider=user[11],
            is_active=user[6],
            created_at=user[8],
        )
