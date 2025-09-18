from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_user_service, get_current_user_id
from app.schemas.artist import ArtistDto
from app.utils.file_upload import upload_profile_image
from app.services.user_service import UserService
from app.schemas.user import (
    UpdateProfileRequest,
    UpdatePreferredArtistsRequest,
    UserDto,
    UserDtoInternal,
)
from app.schemas.auth import SignUpRequest
from app.schemas.common import BaseResponse
from app.core.http_status import HttpStatus

router = APIRouter()


# - MARK: 공개 API
@router.post(
    "",
    response_model=BaseResponse[UserDto],
    responses={
        HttpStatus.CREATED: {
            "model": BaseResponse[UserDto],
            "description": "사용자 생성 성공",
        },
    },
)
async def create_user(
    user_data: SignUpRequest,
    user_service: UserService = Depends(get_user_service),
):
    """사용자 생성 (회원가입)"""
    user = await user_service.create_user(user_data)
    return BaseResponse.ok(data=user, http_status=HttpStatus.CREATED)


# - MARK: 인증 필요 API
@router.get(
    "",
    response_model=BaseResponse[UserDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[UserDto],
            "description": "사용자 정보 조회 성공",
        },
    },
)
async def get_user_info(
    user_id: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 정보 조회 (토큰 필요)"""
    # user_id가 제공되지 않으면 현재 사용자 정보 반환
    target_user_id = user_id if user_id is not None else current_user_id
    user = await user_service.get_user(target_user_id)
    return BaseResponse.ok(data=user)


@router.put(
    "",
    response_model=BaseResponse[UserDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[UserDto],
            "description": "사용자 업데이트 성공",
        },
    },
)
async def update_user_profile(
    nickname: Optional[str] = Form(None),
    intro: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 정보 업데이트 (토큰 필요, 멀티파트 지원)"""
    # 이미지 파일 처리
    profile_image_url = None
    if image:
        try:
            profile_image_url = await upload_profile_image(image)
        except ValueError as e:
            return BaseResponse.error(
                code=HttpStatus.BAD_REQUEST,
                message=str(e),
            )
        except Exception as e:
            return BaseResponse.error(
                code=HttpStatus.INTERNAL_SERVER_ERROR,
                message=f"이미지 업로드 실패: {str(e)}",
            )

    # UpdateProfileRequest 생성
    profile_data = UpdateProfileRequest(
        nickname=nickname, intro=intro, profile_image=profile_image_url
    )

    user = await user_service.update_profile(current_user_id, profile_data)
    return BaseResponse.ok(data=user)


@router.get(
    "/preferred-artists",
    response_model=BaseResponse[List[ArtistDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[List[ArtistDto]],
            "description": "선호 아티스트 조회 성공",
        },
    },
)
async def get_user_preferred_artists(
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 선호 아티스트 조회 (토큰 필요)"""
    artists = await user_service.get_preferred_artists(current_user_id)
    return BaseResponse.ok(data=artists)


@router.put(
    "/preferred-artists",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "선호 아티스트 업데이트 성공",
        },
        HttpStatus.UNAUTHORIZED: {
            "model": BaseResponse[None],
            "description": "인증 실패",
        },
        HttpStatus.INTERNAL_SERVER_ERROR: {
            "model": BaseResponse[None],
            "description": "서버 내부 오류",
        },
    },
)
async def update_user_preferred_artists(
    artists_data: UpdatePreferredArtistsRequest,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 선호 아티스트 업데이트 (토큰 필요)"""
    artists = await user_service.update_preferred_artists(
        current_user_id, artists_data.artist_ids
    )
    return BaseResponse.ok(data={"artists": artists})


# - MARK: 사용자 관리 API
@router.get(
    "/{user_id}",
    response_model=BaseResponse[UserDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[UserDto],
            "description": "사용자 조회 성공",
        },
        HttpStatus.NOT_FOUND: {
            "model": BaseResponse[None],
            "description": "사용자를 찾을 수 없음",
        },
        HttpStatus.INTERNAL_SERVER_ERROR: {
            "model": BaseResponse[None],
            "description": "서버 내부 오류",
        },
    },
)
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """특정 사용자 조회"""
    user = await user_service.get_user(user_id)
    return BaseResponse.ok(data=user)


@router.delete(
    "/{user_id}",
    status_code=HttpStatus.NO_CONTENT,
    responses={
        HttpStatus.NO_CONTENT: {
            "description": "사용자 삭제 성공 (No Content)",
        },
        HttpStatus.UNAUTHORIZED: {
            "model": BaseResponse[None],
            "description": "인증 실패",
        },
        HttpStatus.NOT_FOUND: {
            "model": BaseResponse[None],
            "description": "사용자를 찾을 수 없음",
        },
        HttpStatus.INTERNAL_SERVER_ERROR: {
            "model": BaseResponse[None],
            "description": "서버 내부 오류",
        },
    },
)
async def delete_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 삭제 (토큰 필요)"""
    # TODO: 사용자 삭제 로직 구현. 현재는 자신의 계정만 삭제 가능
    if user_id != current_user_id:
        raise HTTPException(
            status_code=HttpStatus.FORBIDDEN,
            detail="자신의 계정만 삭제할 수 있습니다",
        )
    return BaseResponse.ok(http_status=HttpStatus.NO_CONTENT)


# - MARK: 사용자 차단 API
@router.post(
    "/blocks/{user_id}",
    response_model=BaseResponse[None],
    responses={
        HttpStatus.OK: {"model": BaseResponse[None], "description": "사용자 차단 성공"},
        HttpStatus.UNAUTHORIZED: {
            "model": BaseResponse[None],
            "description": "인증 실패",
        },
        HttpStatus.INTERNAL_SERVER_ERROR: {
            "model": BaseResponse[None],
            "description": "서버 내부 오류",
        },
    },
)
async def block_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 차단 (토큰 필요)"""
    # TODO: 사용자 차단 로직 구현
    return BaseResponse.ok(data=None)


@router.get(
    "/blocks",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "차단된 사용자 목록 조회 성공",
        },
        HttpStatus.UNAUTHORIZED: {
            "model": BaseResponse[None],
            "description": "인증 실패",
        },
        HttpStatus.INTERNAL_SERVER_ERROR: {
            "model": BaseResponse[None],
            "description": "서버 내부 오류",
        },
    },
)
async def get_blocked_users(
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """차단된 사용자 목록 조회 (토큰 필요)"""
    # TODO: 차단된 사용자 목록 조회 로직 구현
    blocked_users: List[UserDto] = []  # 실제 구현 필요
    return BaseResponse.ok(data={"users": blocked_users})


@router.delete(
    "/blocks/{user_id}",
    status_code=HttpStatus.NO_CONTENT,
    responses={
        HttpStatus.NO_CONTENT: {
            "description": "사용자 차단 해제 성공 (No Content)",
        },
        HttpStatus.UNAUTHORIZED: {
            "model": BaseResponse[None],
            "description": "인증 실패",
        },
        HttpStatus.INTERNAL_SERVER_ERROR: {
            "model": BaseResponse[None],
            "description": "서버 내부 오류",
        },
    },
)
async def unblock_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    return BaseResponse.ok(http_status=HttpStatus.NO_CONTENT)


# - MARK: 내부용 API
@router.get(
    "/internal/all",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "사용자 목록 조회 성공",
        },
        HttpStatus.INTERNAL_SERVER_ERROR: {
            "model": BaseResponse[None],
            "description": "서버 내부 오류",
        },
    },
    tags=["internal"],
    summary="모든 사용자 조회 (내부용)",
    description="⚠️ 내부용 API - 모든 사용자 목록을 조회합니다. 개발/테스트 목적으로만 사용됩니다.",
)
async def get_all_users(
    user_service: UserService = Depends(get_user_service),
):
    """모든 사용자 조회 (내부용)"""
    users = await user_service.get_users()
    return BaseResponse.ok(data={"users": users})


@router.get(
    "/internal/{user_id}",
    response_model=BaseResponse[UserDtoInternal],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[UserDtoInternal],
            "description": "사용자 조회 성공",
        },
        HttpStatus.NOT_FOUND: {
            "model": BaseResponse[None],
            "description": "사용자를 찾을 수 없음",
        },
        HttpStatus.INTERNAL_SERVER_ERROR: {
            "model": BaseResponse[None],
            "description": "서버 내부 오류",
        },
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
    user = await user_service.get_user_internal(user_id)
    return BaseResponse.ok(data=user)
