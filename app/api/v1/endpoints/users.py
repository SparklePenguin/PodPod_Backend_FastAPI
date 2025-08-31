from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_user_service, get_current_user_id
from app.services.user_service import UserService
from app.schemas.user import (
    UpdateProfileRequest,
    UpdatePreferredArtistsRequest,
    UserDto,
    UserDtoInternal,
)
from app.schemas.auth import SignUpRequest
from app.schemas.common import SuccessResponse, ErrorResponse

router = APIRouter()


# - MARK: 공개 API
@router.post(
    "/",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": UserDto, "description": "사용자 생성 성공"},
        400: {"model": ErrorResponse, "description": "이메일 중복"},
        422: {"model": ErrorResponse, "description": "입력 데이터 검증 실패"},
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="user_creation_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


# - MARK: 인증 필요 API
@router.get(
    "/",
    response_model=SuccessResponse,
    responses={
        200: {"model": UserDto, "description": "사용자 정보 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def get_user_info(
    user_id: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 정보 조회 (토큰 필요)"""
    try:
        # user_id가 제공되지 않으면 현재 사용자 정보 반환
        target_user_id = user_id if user_id is not None else current_user_id
        user = await user_service.get_user(target_user_id)
        return SuccessResponse(
            code=200, message="user_retrieved_successfully", data={"user": user}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="user_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


@router.put(
    "/",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "프로필 업데이트 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def update_user_profile(
    profile_data: UpdateProfileRequest,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 프로필 업데이트 (토큰 필요)"""
    try:
        user = await user_service.update_profile(current_user_id, profile_data)
        return SuccessResponse(
            code=200, message="profile_updated_successfully", data={"user": user}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="profile_update_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


@router.get(
    "/preferred-artists",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "선호 아티스트 조회 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def get_user_preferred_artists(
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 선호 아티스트 조회 (토큰 필요)"""
    try:
        artists = await user_service.get_preferred_artists(current_user_id)
        return SuccessResponse(
            code=200,
            message="preferred_artists_retrieved_successfully",
            data={"artists": artists},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="preferred_artists_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


@router.put(
    "/preferred-artists",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "선호 아티스트 업데이트 성공"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def update_user_preferred_artists(
    artists_data: UpdatePreferredArtistsRequest,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 선호 아티스트 업데이트 (토큰 필요)"""
    try:
        artists = await user_service.update_preferred_artists(
            current_user_id, artists_data.artist_ids
        )
        return SuccessResponse(
            code=200,
            message="preferred_artists_updated_successfully",
            data={"artists": artists},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="preferred_artists_update_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


# - MARK: 내부용 API
@router.get(
    "/all",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "사용자 목록 조회 성공"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    tags=["internal"],
    summary="모든 사용자 조회 (내부용)",
    description="⚠️ 내부용 API - 모든 사용자 목록을 조회합니다. 개발/테스트 목적으로만 사용됩니다.",
)
async def get_all_users(
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
                error_code="users_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


@router.get(
    "/{user_id}",
    response_model=SuccessResponse,
    responses={
        200: {"model": UserDtoInternal, "description": "사용자 조회 성공"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
    tags=["internal"],
    summary="특정 사용자 조회 (내부용)",
    description="⚠️ 내부용 API - 특정 사용자의 정보를 조회합니다. 개발/테스트 목적으로만 사용됩니다.",
)
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """특정 사용자 조회 (내부용)"""
    try:
        user = await user_service.get_user_internal(user_id)
        return SuccessResponse(
            code=200, message="user_retrieved_successfully", data={"user": user}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="user_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )
