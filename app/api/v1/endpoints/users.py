from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api.deps import get_user_service
from app.services.user_service import UserService
from app.schemas.user import UserResponse
from app.schemas.auth import RegisterRequest, ErrorResponse

router = APIRouter()
security = HTTPBearer()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "이메일 중복"},
        422: {"description": "입력 데이터 검증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def create_user(
    user_data: RegisterRequest,
    user_service: UserService = Depends(get_user_service),
):
    """사용자 생성 (회원가입)"""
    return await user_service.create_user(user_data)


@router.get(
    "/",
    response_model=List[UserResponse],
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
)
async def get_users(
    user_service: UserService = Depends(get_user_service),
):
    """모든 사용자 조회 (토큰 필요)"""
    return await user_service.get_users()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """특정 사용자 조회 (토큰 필요)"""
    return await user_service.get_user(user_id)
