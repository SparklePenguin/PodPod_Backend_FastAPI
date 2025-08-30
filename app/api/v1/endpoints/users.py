from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.api.deps import get_user_service
from app.services.user_service import UserService
from app.schemas.user import (
    UpdateProfileRequest,
    UpdatePreferredArtistsRequest,
)
from app.schemas.auth import SignUpRequest
from app.schemas.common import SuccessResponse, ErrorResponse

router = APIRouter()
security = HTTPBearer()


# - MARK: 공개 API
@router.post(
    "/",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": SuccessResponse, "description": "사용자 생성 성공"},
        400: {"model": ErrorResponse, "description": "이메일 중복"},
        422: {"description": "입력 데이터 검증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def create_user(
    user_data: SignUpRequest,
    user_service: UserService = Depends(get_user_service),
):
    """사용자 생성 (회원가입)"""
    try:
        user = await user_service.create_user(user_data)
        return SuccessResponse(
            code=201, message="user_created_successfully", data={"user": user}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="user_creation_failed",
                status=500,
                message=str(e),
            ),
        )


# - MARK: 인증 필요 API
@router.get(
    "/me",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "내 정보 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
)
async def get_my_profile(
    user_service: UserService = Depends(get_user_service),
):
    """내 프로필 조회 (토큰 필요)"""
    # TODO: 토큰에서 user_id 추출하여 사용
    pass


@router.put(
    "/me",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "프로필 업데이트 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
)
async def update_my_profile(
    profile_data: UpdateProfileRequest,
    user_service: UserService = Depends(get_user_service),
):
    """내 프로필 업데이트 (토큰 필요)"""
    # TODO: 토큰에서 user_id 추출하여 사용
    pass


@router.get(
    "/me/preferred-artists",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "선호 아티스트 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
)
async def get_my_preferred_artists(
    user_service: UserService = Depends(get_user_service),
):
    """내 선호 아티스트 조회 (토큰 필요)"""
    # TODO: 토큰에서 user_id 추출하여 사용
    pass


@router.put(
    "/me/preferred-artists",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "선호 아티스트 업데이트 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
)
async def update_my_preferred_artists(
    artists_data: UpdatePreferredArtistsRequest,
    user_service: UserService = Depends(get_user_service),
):
    """내 선호 아티스트 업데이트 (토큰 필요)"""
    # TODO: 토큰에서 user_id 추출하여 사용
    pass


# - MARK: 내부용 API
@router.get(
    "/",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "사용자 목록 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
    tags=["internal"],
    summary="모든 사용자 조회 (내부용)",
    description="⚠️ 내부용 API - 모든 사용자 목록을 조회합니다. 개발/테스트 목적으로만 사용됩니다.",
)
async def get_users(
    user_service: UserService = Depends(get_user_service),
):
    """모든 사용자 조회 (내부용)"""
    try:
        users = await user_service.get_users()
        return SuccessResponse(
            code=200, message="users_retrieved_successfully", data={"users": users}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="users_retrieval_failed",
                status=500,
                message=str(e),
            ),
        )


@router.get(
    "/{user_id}",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "사용자 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    dependencies=[Depends(security)],
    tags=["internal"],
    summary="특정 사용자 조회 (내부용)",
    description="⚠️ 내부용 API - 특정 사용자의 정보를 조회합니다. 개발/테스트 목적으로만 사용됩니다.",
)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """특정 사용자 조회 (내부용)"""
    try:
        user = await user_service.get_user(user_id)
        return SuccessResponse(
            code=200, message="user_retrieved_successfully", data={"user": user}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="user_retrieval_failed",
                status=500,
                message=str(e),
            ),
        )
