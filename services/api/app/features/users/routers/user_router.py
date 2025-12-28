from typing import List

from app.utils.file_upload import upload_profile_image
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import BaseResponse, PageDto
from app.core.database import get_session
from app.core.http_status import HttpStatus
from app.deps.auth import get_current_user_id
from app.features.artists.schemas import ArtistDto
from app.features.follow.schemas import SimpleUserDto
from app.features.auth.schemas.sign_up_request import SignUpRequest
from app.features.users.schemas import (
    AcceptTermsRequest,
    BlockUserResponse,
    UpdatePreferredArtistsRequest,
    UpdateProfileRequest,
    UpdateUserNotificationSettingsRequest,
    UserDto,
    UserDtoInternal,
    UserNotificationSettingsDto,
)
from app.features.users.services.user_service import UserService

router = APIRouter()


# - MARK: 인증 필요 API
@router.post(
    "/terms",
    response_model=BaseResponse[UserDto],
    description="사용자가 약관에 동의합니다.",
    tags=["users"],
)
async def accept_terms(
    request: AcceptTermsRequest,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    user = await service.accept_terms(current_user_id, request.terms_accepted)
    return BaseResponse.ok(
        data=user,
        message_ko="약관 동의가 완료되었습니다.",
        message_en="Terms accepted successfully.",
        http_status=HttpStatus.OK,
    )


# - MARK: 공개 API
@router.post(
    "",
    response_model=BaseResponse[UserDto],
    description="새로운 사용자를 생성합니다 (회원가입).",
    tags=["users"],
)
async def create_user(
    user_data: SignUpRequest, session: AsyncSession = Depends(get_session)
):
    service = UserService(session)
    user = await service.create_user(
        email=user_data.email,
        name=user_data.name,
        nickname=user_data.nickname,
        profile_image=user_data.profile_image,
        auth_provider=user_data.auth_provider,
        auth_provider_id=user_data.auth_provider_id,
        fcm_token=user_data.fcm_token,
        password=user_data.password,
    )
    return BaseResponse.ok(data=user, http_status=HttpStatus.CREATED)


@router.get(
    "",
    response_model=BaseResponse[UserDto],
    description="현재 로그인한 사용자 또는 특정 사용자의 정보를 조회합니다.",
    tags=["users"],
)
async def get_user_info(
    user_id: int | None = Query(
        None, serialization_alias="userId", description="조회할 사용자 ID (없으면 본인)"
    ),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    # user_id가 제공되지 않으면 현재 사용자 정보 반환
    target_user_id = user_id if user_id is not None else current_user_id

    if target_user_id == current_user_id:
        # 본인 정보 조회
        user = await service.get_user(target_user_id)
    else:
        # 다른 사용자 정보 조회 (팔로우 통계 포함)
        user = await service.get_user_with_follow_stats(target_user_id, current_user_id)

    return BaseResponse.ok(data=user)


@router.put(
    "",
    response_model=BaseResponse[UserDto],
    description="사용자 정보 업데이트 (토큰 필요, 파일 업로드 또는 경로 지정 가능)",
)
async def update_user_profile(
    nickname: str | None = Form(None),
    intro: str | None = Form(None),
    profile_image_path: str | None = Form(None, serialization_alias="profileImagePath"),
    image: UploadFile | None = File(None),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    # 이미지 처리: 파일 업로드 또는 경로 지정
    profile_image_url = None

    # 파일 업로드가 있는 경우
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
    # 경로가 제공된 경우
    elif profile_image_path:
        profile_image_url = profile_image_path

    # UpdateProfileRequest 생성
    profile_data = UpdateProfileRequest(
        nickname=nickname, intro=intro, profile_image=profile_image_url
    )
    service = UserService(session)
    user = await service.update_profile(current_user_id, profile_data)
    return BaseResponse.ok(data=user)


@router.get(
    "/preferred-artists",
    response_model=BaseResponse[List[ArtistDto]],
    description="사용자 선호 아티스트 조회 (토큰 필요)",
    tags=["users"],
)
async def get_user_preferred_artists(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    artists = await service.get_preferred_artists(current_user_id)
    return BaseResponse.ok(data=artists)


@router.put(
    "/preferred-artists",
    response_model=BaseResponse[dict],
    description="현재 사용자의 선호 아티스트 목록을 업데이트합니다.",
    tags=["users"],
)
async def update_user_preferred_artists(
    artists_data: UpdatePreferredArtistsRequest,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    artists = await service.update_preferred_artists(
        current_user_id, artists_data.artist_ids
    )
    return BaseResponse.ok(data={"artists": artists})


# - MARK: 사용자 차단 API (동적 경로보다 먼저 정의)
@router.post(
    "/blocks/{user_id}",
    response_model=BaseResponse[BlockUserResponse],
    description="사용자 차단 (토큰 필요) - 팔로우 관계도 함께 삭제됨",
)
async def block_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        # 자기 자신을 차단하려는 경우
        if user_id == current_user_id:
            return BaseResponse(
                data=None,
                http_status=400,
                message_ko="자기 자신을 차단할 수 없습니다.",
                message_en="Cannot block yourself.",
                error_key="CANNOT_BLOCK_SELF",
                error_code=4003,
                dev_note=None,
            )
        service = UserService(session)
        block_response = await service.block_user(current_user_id, user_id)

        if not block_response:
            return BaseResponse(
                data=None,
                http_status=404,
                message_ko="차단할 사용자를 찾을 수 없습니다.",
                message_en="User to block not found.",
                error_key="USER_NOT_FOUND",
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
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            dev_note=None,
        )


@router.get(
    "/blocks",
    response_model=BaseResponse[PageDto[SimpleUserDto]],
    description="차단된 사용자 목록 조회 (토큰 필요)",
    tags=["users"],
)
async def get_blocked_users(
    page: int = Query(
        1, ge=1, serialization_alias="page", description="페이지 번호 (1부터 시작)"
    ),
    size: int = Query(
        20, ge=1, le=100, serialization_alias="size", description="페이지 크기 (1~100)"
    ),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        service = UserService(session)
        blocked_users_page = await service.get_blocked_users(
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

        print(f"사용자 차단 목록 조회 오류: {e}")
        traceback.print_exc()
        return BaseResponse(
            data=None,
            http_status=500,
            message_ko="사용자 차단 목록 조회 중 오류가 발생했습니다.",
            message_en="An error occurred while retrieving blocked users list.",
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            dev_note=None,
        )


@router.delete(
    "/blocks/{user_id}",
    response_model=BaseResponse[bool],
    description="사용자 차단 해제 (토큰 필요)",
)
async def unblock_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        service = UserService(session)
        success = await service.unblock_user(current_user_id, user_id)

        if not success:
            return BaseResponse(
                data=None,
                http_status=404,
                message_ko="차단 관계를 찾을 수 없습니다.",
                message_en="Block relationship not found.",
                error_key="BLOCK_NOT_FOUND",
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
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            dev_note=None,
        )


# - MARK: 사용자 관리 API
@router.put(
    "/fcm-token",
    response_model=BaseResponse[dict],
    description="FCM 토큰 업데이트 (토큰 필요)",
    tags=["users"],
)
async def update_fcm_token(
    fcm_token: str = Query(..., serialization_alias="fcmToken", description="FCM 토큰"),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    from app.features.users.repositories import UserRepository

    user_crud = UserRepository(session)
    await user_crud.update_profile(current_user_id, {"fcm_token": fcm_token})

    return BaseResponse.ok(
        data={"updated": True},
        message_ko="FCM 토큰이 업데이트되었습니다.",
        message_en="FCM token updated successfully.",
    )


@router.get(
    "/{user_id}", response_model=BaseResponse[UserDto], description="특정 사용자 조회"
)
async def get_user_by_id(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    user = await service.get_user_with_follow_stats(user_id, current_user_id)
    return BaseResponse.ok(data=user)


@router.delete(
    "",
    status_code=HttpStatus.NO_CONTENT,
    description="사용자 삭제 (userId 또는 토큰 필요)",
    tags=["users"],
)
async def delete_user(
    user_id: int | None = Query(
        None, serialization_alias="userId", description="삭제할 사용자 ID"
    ),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    # userId가 있으면 해당 유저 삭제
    if user_id is not None:
        target_user_id = user_id
    # userId 없으면 토큰에서 추출한 유저 삭제
    else:
        target_user_id = current_user_id

    try:
        service = UserService(session)
        await service.delete_user(target_user_id)
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
    description="모든 사용자 조회 (내부용)",
    tags=["internal"],
)
async def get_all_users(session: AsyncSession = Depends(get_session)):
    service = UserService(session)
    users = await service.get_users()
    return BaseResponse.ok(data={"users": users})


@router.get(
    "/internal/{user_id}",
    response_model=BaseResponse[UserDtoInternal],
    description="특정 사용자 조회 (내부용)",
    tags=["internal"],
)
async def get_user_by_id_internal(
    user_id: int, session: AsyncSession = Depends(get_session)
):
    service = UserService(session)
    user = await service.get_user_internal(user_id)
    return BaseResponse.ok(data=user)


# """
# 사용자 알림 설정 API 엔드포인트
# """


# from app.api.deps import get_current_user_id, get_db
# from app.features.users.repositories import UserNotificationSettingsRepository
# from app.features.users.schemas import (
#     UserNotificationSettingsDto,
#     UpdateUserNotificationSettingsRequest,
# )
# from app.schemas.common.base_response import BaseResponse
# from app.core.http_status import HttpStatus


@router.get(
    "/notification-settings",
    response_model=BaseResponse[UserNotificationSettingsDto],
    description="사용자의 알림 설정을 조회합니다.",
)
async def get_notification_settings(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    from app.features.users.repositories import (
        UserNotificationSettingsRepository,  # Temporary import for this section
    )

    crud = UserNotificationSettingsRepository(db)

    # 사용자 설정 조회
    settings = await crud.get_by_user_id(current_user_id)

    if not settings:
        # 설정이 없으면 기본 설정 생성
        settings = await crud.create_default_settings(current_user_id)

    # DTO 변환
    do_not_disturb_start_value = getattr(settings, "do_not_disturb_start", None)
    do_not_disturb_end_value = getattr(settings, "do_not_disturb_end", None)

    settings_dto = UserNotificationSettingsDto(
        id=getattr(settings, "id"),
        user_id=getattr(settings, "user_id"),
        wake_up_alarm=bool(getattr(settings, "notice_enabled", False)),
        bus_alert=bool(getattr(settings, "chat_enabled", False)),
        party_alert=bool(getattr(settings, "pod_enabled", False)),
        community_alert=bool(getattr(settings, "community_enabled", False)),
        product_alarm=bool(getattr(settings, "marketing_enabled", False)),
        do_not_disturb_enabled=bool(getattr(settings, "do_not_disturb_enabled", False)),
        start_time=(
            int(
                do_not_disturb_start_value.hour * 3600
                + do_not_disturb_start_value.minute * 60
            )
            * 1000
            if do_not_disturb_start_value is not None
            else None
        ),
        end_time=(
            int(
                do_not_disturb_end_value.hour * 3600
                + do_not_disturb_end_value.minute * 60
            )
            * 1000
            if do_not_disturb_end_value is not None
            else None
        ),
        marketing_enabled=bool(getattr(settings, "marketing_enabled", False)),
    )

    return BaseResponse.ok(
        data=settings_dto,
        message_ko="알림 설정을 조회했습니다.",
        http_status=HttpStatus.OK,
    )


@router.patch(
    "/notification-settings",
    response_model=BaseResponse[UserNotificationSettingsDto],
    description="사용자의 알림 설정을 수정합니다. 원하는 필드만 수정할 수 있습니다.",
)
async def update_notification_settings(
    update_data: UpdateUserNotificationSettingsRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    from app.features.users.repositories import (
        UserNotificationSettingsRepository,  # Temporary import for this section
    )

    crud = UserNotificationSettingsRepository(db)

    # 기존 설정 확인
    settings = await crud.get_by_user_id(current_user_id)
    if not settings:
        # 설정이 없으면 기본 설정 생성
        settings = await crud.create_default_settings(current_user_id)

    # 설정 업데이트
    updated_settings = await crud.update_settings(current_user_id, update_data)
    if not updated_settings:
        from app.features.users.exceptions import UserNotFoundException

        raise UserNotFoundException(current_user_id)

    # DTO 변환
    do_not_disturb_start_value = getattr(updated_settings, "do_not_disturb_start", None)
    do_not_disturb_end_value = getattr(updated_settings, "do_not_disturb_end", None)

    settings_dto = UserNotificationSettingsDto(
        id=getattr(updated_settings, "id"),
        user_id=getattr(updated_settings, "user_id"),
        wake_up_alarm=bool(getattr(updated_settings, "notice_enabled", False)),
        bus_alert=bool(getattr(updated_settings, "chat_enabled", False)),
        party_alert=bool(getattr(updated_settings, "pod_enabled", False)),
        community_alert=bool(getattr(updated_settings, "community_enabled", False)),
        product_alarm=bool(getattr(updated_settings, "marketing_enabled", False)),
        do_not_disturb_enabled=bool(
            getattr(updated_settings, "do_not_disturb_enabled", False)
        ),
        start_time=(
            int(
                do_not_disturb_start_value.hour * 3600
                + do_not_disturb_start_value.minute * 60
            )
            * 1000
            if do_not_disturb_start_value is not None
            else None
        ),
        end_time=(
            int(
                do_not_disturb_end_value.hour * 3600
                + do_not_disturb_end_value.minute * 60
            )
            * 1000
            if do_not_disturb_end_value is not None
            else None
        ),
        marketing_enabled=bool(getattr(updated_settings, "marketing_enabled", False)),
    )

    return BaseResponse.ok(
        data=settings_dto,
        message_ko="알림 설정을 수정했습니다.",
        http_status=HttpStatus.OK,
    )
