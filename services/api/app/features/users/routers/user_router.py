from typing import List

from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.service import get_user_service
from app.features.artists.schemas import ArtistDto
from app.features.auth.schemas.sign_up_request import SignUpRequest
from app.features.users.exceptions import ImageUploadException
from app.features.users.schemas import (
    AcceptTermsRequest,
    UpdatePreferredArtistsRequest,
    UpdateProfileRequest,
    UserDetailDto,
)
from app.features.users.services.user_service import UserService
from app.utils.file_upload import upload_profile_image
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)

router = APIRouter()


# - MARK: 약관 동의
@router.post(
    "/terms",
    response_model=BaseResponse[UserDetailDto],
    description="사용자 약관 동의",
)
async def accept_terms(
    request: AcceptTermsRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    result = await service.accept_terms(current_user_id, request.terms_accepted)
    return BaseResponse.ok(
        data=result,
        message_ko="약관 동의가 완료되었습니다.",
        message_en="Terms accepted successfully.",
        http_status=status.HTTP_200_OK,
    )


# - MARK: 사용자 생성
@router.post(
    "",
    response_model=BaseResponse[UserDetailDto],
    description="사용자 생성 (회원가입)",
)
async def create_user(
    user_data: SignUpRequest,
    service: UserService = Depends(get_user_service),
):
    result = await service.create_user(
        email=user_data.email,
        name=user_data.username,
        nickname=user_data.nickname,
        profile_image=user_data.profile_image,
        auth_provider=user_data.auth_provider,
        auth_provider_id=user_data.auth_provider_id,
        fcm_token=user_data.fcm_token,
        password=user_data.password,
    )
    return BaseResponse.ok(data=result, http_status=status.HTTP_201_CREATED)


# - MARK: 본인 정보 조회
@router.get(
    "/me",
    response_model=BaseResponse[UserDetailDto],
    description="현재 로그인한 사용자 정보 조회",
)
async def get_my_info(
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    """본인 정보 조회"""
    user = await service.get_user(current_user_id)
    return BaseResponse.ok(data=user)


# - MARK: 사용자 정보 조회
@router.get(
    "/{user_id}",
    response_model=BaseResponse[UserDetailDto],
    description="사용자 정보 조회 (팔로우 통계 포함)",
)
async def get_user_info(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    """다른 사용자 정보 조회 (팔로우 통계 포함)"""
    user = await service.get_user_with_follow_stats(user_id, current_user_id)
    return BaseResponse.ok(data=user)


# - MARK: 사용자 정보 업데이트
@router.put(
    "",
    response_model=BaseResponse[UserDetailDto],
    description="사용자 정보 업데이트",
)
async def update_user_profile(
    nickname: str | None = Form(None),
    intro: str | None = Form(None),
    profile_image_path: str | None = Form(None, alias="profileImagePath"),
    image: UploadFile | None = File(None),
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    # 이미지 처리: 파일 업로드 또는 경로 지정
    profile_image_url = None

    # 파일 업로드가 있는 경우
    if image:
        try:
            profile_image_url = await upload_profile_image(image)
        except ValueError as e:
            raise ImageUploadException(message=str(e))
        except Exception as e:
            raise ImageUploadException(message=f"이미지 업로드 실패: {str(e)}")
    # 경로가 제공된 경우
    elif profile_image_path:
        profile_image_url = profile_image_path

    # UpdateProfileRequest 생성
    profile_data = UpdateProfileRequest(
        nickname=nickname, intro=intro, profile_image=profile_image_url
    )
    user = await service.update_profile(current_user_id, profile_data)
    return BaseResponse.ok(data=user)


# - MARK: 선호 아티스트 조회
@router.get(
    "/preferred-artists",
    response_model=BaseResponse[List[ArtistDto]],
    description="사용자 선호 아티스트 조회 (토큰 필요)",
)
async def get_user_preferred_artists(
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    artists = await service.get_preferred_artists(current_user_id)
    return BaseResponse.ok(data=artists)


# - MARK: 선호 아티스트 업데이트
@router.put(
    "/preferred-artists",
    response_model=BaseResponse[dict],
    description="현재 사용자의 선호 아티스트 목록을 업데이트합니다.",
)
async def update_user_preferred_artists(
    artists_data: UpdatePreferredArtistsRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    artists = await service.update_preferred_artists(
        current_user_id, artists_data.artist_ids
    )
    return BaseResponse.ok(data={"artists": artists})


# - MARK: FCM 토큰 업데이트
@router.put(
    "/fcm-token",
    response_model=BaseResponse[UserDetailDto],
    description="FCM 토큰 업데이트 (토큰 필요)",
)
async def update_fcm_token(
    fcm_token: str = Query(..., alias="fcmToken", description="FCM 토큰"),
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    await service.update_fcm_token(current_user_id, fcm_token)

    return BaseResponse.ok(
        data={"updated": True},
        message_ko="FCM 토큰이 업데이트되었습니다.",
        message_en="FCM token updated successfully.",
    )


# - MARK: 본인 계정 삭제
@router.delete(
    "/me",
    description="현재 로그인한 사용자 삭제",
)
async def delete_my_account(
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    """본인 계정 삭제"""
    try:
        await service.delete_user(current_user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        # 사용자가 존재하지 않는 경우에도 204 No Content 반환
        # (이미 삭제된 상태와 동일하므로)
        if "USER_NOT_FOUND" in str(e):
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        # 다른 오류는 그대로 전파
        raise e


# - MARK: 특정 사용자 삭제
@router.delete(
    "/{user_id}",
    description="특정 사용자 삭제",
)
async def delete_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    """특정 사용자 삭제"""
    try:
        await service.delete_user(user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        # 사용자가 존재하지 않는 경우에도 204 No Content 반환
        # (이미 삭제된 상태와 동일하므로)
        if "USER_NOT_FOUND" in str(e):
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        # 다른 오류는 그대로 전파
        raise e
