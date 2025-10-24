from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Query,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.api.deps import (
    get_user_service,
    get_current_user_id,
)
from app.schemas.artist import ArtistDto
from app.utils.file_upload import upload_profile_image
from app.services.user_service import UserService
from app.schemas.user import (
    UpdateProfileRequest,
    UpdatePreferredArtistsRequest,
    UserDto,
    UserDtoInternal,
    BlockUserResponse,
)
from app.schemas.follow import SimpleUserDto
from app.schemas.common.page_dto import PageDto
from app.schemas.auth import SignUpRequest
from app.schemas.common import BaseResponse
from app.core.http_status import HttpStatus
from app.core.logging_config import get_logger

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
    summary="사용자 생성",
    description="새로운 사용자를 생성합니다 (회원가입).",
    tags=["users"],
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
    summary="사용자 정보 조회",
    description="현재 로그인한 사용자 또는 특정 사용자의 정보를 조회합니다.",
    tags=["users"],
)
async def get_user_info(
    user_id: Optional[int] = Query(
        None, alias="userId", description="조회할 사용자 ID (없으면 본인)"
    ),
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 정보 조회 (토큰 필요)"""
    # user_id가 제공되지 않으면 현재 사용자 정보 반환
    target_user_id = user_id if user_id is not None else current_user_id

    if target_user_id == current_user_id:
        # 본인 정보 조회
        user = await user_service.get_user(target_user_id)
    else:
        # 다른 사용자 정보 조회 (팔로우 통계 포함)
        user = await user_service.get_user_with_follow_stats(
            target_user_id, current_user_id
        )

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
                error_key="IMAGE_UPLOAD_ERROR",
                error_code=400,
                http_status=HttpStatus.BAD_REQUEST,
                message_ko=str(e),
                message_en="Image upload error",
            )
        except Exception as e:
            return BaseResponse.error(
                error_key="INTERNAL_SERVER_ERROR",
                error_code=500,
                http_status=HttpStatus.INTERNAL_SERVER_ERROR,
                message_ko=f"이미지 업로드 실패: {str(e)}",
                message_en="Image upload failed",
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
    summary="선호 아티스트 조회",
    description="현재 사용자의 선호 아티스트 목록을 조회합니다.",
    tags=["users"],
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
    summary="선호 아티스트 업데이트",
    description="현재 사용자의 선호 아티스트 목록을 업데이트합니다.",
    tags=["users"],
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


# - MARK: 사용자 차단 API (동적 경로보다 먼저 정의)
@router.post(
    "/blocks/{user_id}",
    response_model=BaseResponse[BlockUserResponse],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[BlockUserResponse],
            "description": "사용자 차단 성공",
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
async def block_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 차단 (토큰 필요) - 팔로우 관계도 함께 삭제됨"""
    try:
        # 자기 자신을 차단하려는 경우
        if user_id == current_user_id:
            return BaseResponse(
                data=None,
                http_status=400,
                message_ko="자기 자신을 차단할 수 없습니다.",
                message_en="Cannot block yourself.",
                error="CANNOT_BLOCK_SELF",
                error_code=4003,
                dev_note=None,
            )

        block_response = await user_service.block_user(current_user_id, user_id)

        if not block_response:
            return BaseResponse(
                data=None,
                http_status=404,
                message_ko="차단할 사용자를 찾을 수 없습니다.",
                message_en="User to block not found.",
                error="USER_NOT_FOUND",
                error_code=4004,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=block_response,
            http_status=HttpStatus.OK,
            message_ko="사용자를 차단했습니다. 팔로우 관계도 해제되었습니다.",
            message_en="Successfully blocked the user. Follow relationship also removed.",
        )
    except Exception as e:
        import traceback

        print(f"사용자 차단 오류: {e}")
        traceback.print_exc()
        return BaseResponse(
            data=None,
            http_status=500,
            message_ko="사용자 차단 중 오류가 발생했습니다.",
            message_en="An error occurred while blocking the user.",
            error="INTERNAL_SERVER_ERROR",
            error_code=5000,
            dev_note=None,
        )


@router.get(
    "/blocks",
    response_model=BaseResponse[PageDto[SimpleUserDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[SimpleUserDto]],
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
    summary="차단된 사용자 목록 조회",
    description="현재 사용자가 차단한 사용자 목록을 조회합니다.",
    tags=["users"],
)
async def get_blocked_users(
    page: int = Query(1, ge=1, alias="page", description="페이지 번호 (1부터 시작)"),
    size: int = Query(
        20, ge=1, le=100, alias="size", description="페이지 크기 (1~100)"
    ),
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """차단된 사용자 목록 조회 (토큰 필요)"""
    try:
        blocked_users_page = await user_service.get_blocked_users(
            current_user_id, page, size
        )

        return BaseResponse.ok(
            data=blocked_users_page,
            http_status=HttpStatus.OK,
            message_ko="차단된 사용자 목록을 조회했습니다.",
            message_en="Successfully retrieved blocked users list.",
        )
    except Exception as e:
        import traceback

        print(f"차단된 사용자 목록 조회 오류: {e}")
        traceback.print_exc()
        return BaseResponse(
            data=None,
            http_status=500,
            message_ko="차단된 사용자 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving blocked users list.",
            error="INTERNAL_SERVER_ERROR",
            error_code=5000,
            dev_note=None,
        )


@router.delete(
    "/blocks/{user_id}",
    response_model=BaseResponse[bool],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[bool],
            "description": "사용자 차단 해제 성공",
        },
        HttpStatus.UNAUTHORIZED: {
            "model": BaseResponse[None],
            "description": "인증 실패",
        },
        HttpStatus.NOT_FOUND: {
            "model": BaseResponse[None],
            "description": "차단 관계를 찾을 수 없음",
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
    """사용자 차단 해제 (토큰 필요)"""
    try:
        success = await user_service.unblock_user(current_user_id, user_id)

        if not success:
            return BaseResponse(
                data=None,
                http_status=404,
                message_ko="차단 관계를 찾을 수 없습니다.",
                message_en="Block relationship not found.",
                error="BLOCK_NOT_FOUND",
                error_code=4005,
                dev_note=None,
            )

        return BaseResponse.ok(
            data=True,
            http_status=HttpStatus.OK,
            message_ko="사용자 차단을 해제했습니다.",
            message_en="Successfully unblocked the user.",
        )
    except Exception as e:
        import traceback

        print(f"사용자 차단 해제 오류: {e}")
        traceback.print_exc()
        return BaseResponse(
            data=None,
            http_status=500,
            message_ko="사용자 차단 해제 중 오류가 발생했습니다.",
            message_en="An error occurred while unblocking the user.",
            error="INTERNAL_SERVER_ERROR",
            error_code=5000,
            dev_note=None,
        )


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
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """특정 사용자 조회"""
    user = await user_service.get_user_with_follow_stats(user_id, current_user_id)
    return BaseResponse.ok(data=user)


@router.put(
    "/fcm-token",
    response_model=BaseResponse[dict],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[dict],
            "description": "FCM 토큰 업데이트 성공",
        },
    },
    summary="FCM 토큰 업데이트",
    description="사용자의 FCM 토큰을 업데이트합니다 (푸시 알림용).",
    tags=["users"],
)
async def update_fcm_token(
    fcm_token: str = Query(..., alias="fcmToken", description="FCM 토큰"),
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """FCM 토큰 업데이트 (토큰 필요)"""
    from app.crud.user import UserCRUD

    user_crud = UserCRUD(user_service.db)
    await user_crud.update_profile(current_user_id, {"fcm_token": fcm_token})

    return BaseResponse.ok(
        data={"updated": True},
        message_ko="FCM 토큰이 업데이트되었습니다.",
        message_en="FCM token updated successfully.",
    )


@router.delete(
    "",
    status_code=HttpStatus.NO_CONTENT,
    responses={
        HttpStatus.NO_CONTENT: {
            "description": "사용자 삭제 성공 (No Content)",
        },
        HttpStatus.BAD_REQUEST: {
            "model": BaseResponse[None],
            "description": "userId 또는 토큰이 필요합니다",
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
    summary="사용자 삭제",
    description="사용자 계정을 삭제합니다. userId가 제공되면 해당 사용자를 삭제하고, 없으면 토큰에서 사용자를 확인하여 삭제합니다.",
    tags=["users"],
)
async def delete_user(
    user_id: Optional[int] = Query(
        None, alias="userId", description="삭제할 사용자 ID"
    ),
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """사용자 삭제 (userId 또는 토큰 필요)"""
    # userId가 있으면 해당 유저 삭제
    if user_id is not None:
        target_user_id = user_id
    # userId 없으면 토큰에서 추출한 유저 삭제
    else:
        target_user_id = current_user_id

    try:
        await user_service.delete_user(target_user_id)
        return Response(status_code=HttpStatus.NO_CONTENT)
    except Exception as e:
        # 사용자가 존재하지 않는 경우에도 204 No Content 반환
        # (이미 삭제된 상태와 동일하므로)
        if "USER_NOT_FOUND" in str(e):
            return Response(status_code=HttpStatus.NO_CONTENT)
        # 다른 오류는 그대로 전파
        raise e


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
