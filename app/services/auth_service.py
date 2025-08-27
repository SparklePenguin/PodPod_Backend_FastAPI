from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import UserCRUD
from app.schemas.auth import Token, LoginResponse, RegisterRequest, SocialLoginRequest
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings
from datetime import timedelta


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_crud = UserCRUD(db)

    async def register(self, user_data: RegisterRequest) -> dict:
        """일반 회원가입"""
        try:
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

            return {
                "success": True,
                "message": "회원가입이 완료되었습니다",
                "user_id": user.id,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원가입 실패: {str(e)}",
            )

    async def login(self, login_data) -> LoginResponse:
        """통합 로그인 (이메일 + 소셜)"""
        try:
            # 이메일 로그인인지 소셜 로그인인지 판단
            if login_data.password:
                # 이메일 로그인
                return await self.email_login(login_data.email, login_data.password)
            else:
                # 소셜 로그인
                social_data = SocialLoginRequest(
                    email=login_data.email,
                    auth_provider=login_data.auth_provider,
                    auth_provider_id=login_data.auth_provider_id,
                    username=login_data.username,
                    full_name=login_data.full_name,
                    profile_image=login_data.profile_image,
                )
                return await self.social_login(social_data)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"로그인 실패: {str(e)}",
            )

    async def email_login(self, email: str, password: str) -> LoginResponse:
        """이메일 로그인"""
        try:
            # 사용자 확인
            user = await self.user_crud.get_by_email(email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 잘못되었습니다",
                )

            # 비밀번호 확인
            from app.core.security import verify_password

            if not verify_password(password, user[3]):  # hashed_password 필드
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 잘못되었습니다",
                )

            # 액세스 토큰 생성
            access_token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = create_access_token(
                data={"sub": user[2]}, expires_delta=access_token_expires
            )

            # 응답 데이터 구성
            token_data = Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

            user_data = {
                "id": user[0],
                "email": user[2],
                "username": user[1],
                "full_name": user[4],
                "auth_provider": user[11],
            }

            return LoginResponse(
                success=True,
                message="로그인이 완료되었습니다",
                data=token_data,
                user=user_data,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"로그인 실패: {str(e)}",
            )

    async def social_login(self, login_data: SocialLoginRequest) -> LoginResponse:
        """소셜 로그인 (회원가입 + 로그인)"""
        try:
            # 기존 사용자 확인
            existing_user = await self.user_crud.get_by_email(login_data.email)

            if existing_user:
                # 기존 사용자 로그인
                user = existing_user
            else:
                # 새 사용자 생성
                user_dict = login_data.dict()
                user_dict["auth_provider"] = login_data.auth_provider
                user = await self.user_crud.create(user_dict)

            # 액세스 토큰 생성
            access_token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = create_access_token(
                data={"sub": user.email if hasattr(user, "email") else user[2]},
                expires_delta=access_token_expires,
            )

            # 응답 데이터 구성
            token_data = Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

            user_data = {
                "id": user.id if hasattr(user, "id") else user[0],
                "email": user.email if hasattr(user, "email") else user[2],
                "username": user.username if hasattr(user, "username") else user[1],
                "full_name": user.full_name if hasattr(user, "full_name") else user[4],
                "auth_provider": (
                    user.auth_provider if hasattr(user, "auth_provider") else user[11]
                ),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"소셜 로그인 실패: {str(e)}",
            )

    async def logout(self, token: str) -> dict:
        """로그아웃 (토큰 무효화)"""
        # 실제 구현에서는 토큰을 블랙리스트에 추가하거나 Redis에서 삭제
        return {"success": True, "message": "로그아웃이 완료되었습니다"}

    async def refresh_token(self, refresh_token: str) -> Token:
        """토큰 갱신"""
        # 실제 구현에서는 refresh token을 검증하고 새로운 access token 발급
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="토큰 갱신 기능은 아직 구현되지 않았습니다",
        )
