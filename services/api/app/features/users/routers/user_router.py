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

from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.providers import (
    get_block_user_use_case,
    get_follow_use_case,
    get_user_use_case,
)
from app.features.auth.schemas import SignUpRequest
from app.features.follow.use_cases.follow_use_case import FollowUseCase
from app.features.users.exceptions import ImageUploadException
from app.features.users.routers import UserRouterRootLabel
from app.features.users.schemas import (
    AcceptTermsRequest,
    UpdateProfileRequest,
    UserDetailDto,
    UserDto,
)
from app.features.users.use_cases.block_user_use_case import BlockUserUseCase
from app.features.users.use_cases.user_use_case import UserUseCase
from app.utils.file_upload import upload_profile_image


class UserCommonRouter:
    router = APIRouter(prefix=UserRouterRootLabel.PREFIX, tags=[UserRouterRootLabel.TAG])

    @staticmethod
    @router.get(
        "/types",
        response_model=BaseResponse[dict],
        description="사용자 조회 가능한 타입 목록",
    )
    async def get_user_types():
        """사용 가능한 사용자 조회 타입 목록"""
        types = {
            "types": [
                {
                    "value": "recommended",
                    "label_ko": "추천 사용자",
                    "label_en": "Recommended Users",
                    "description_ko": "추천 사용자 목록",
                    "description_en": "List of recommended users",
                },
                {
                    "value": "followings",
                    "label_ko": "팔로우하는 사용자",
                    "label_en": "Following Users",
                    "description_ko": "내가 팔로우하는 사용자 목록",
                    "description_en": "List of users I follow",
                },
                {
                    "value": "followers",
                    "label_ko": "팔로워",
                    "label_en": "Followers",
                    "description_ko": "나를 팔로우하는 사용자 목록",
                    "description_en": "List of users who follow me",
                },
                {
                    "value": "blocks",
                    "label_ko": "차단된 사용자",
                    "label_en": "Blocked Users",
                    "description_ko": "차단한 사용자 목록",
                    "description_en": "List of blocked users",
                },
            ]
        }
        return BaseResponse.ok(
            data=types,
            message_ko="사용자 조회 타입 목록을 조회했습니다.",
            message_en="Successfully retrieved user types.",
        )


class UserSearchRouter:
    router = APIRouter(prefix=UserRouterRootLabel.PREFIX, tags=[UserRouterRootLabel.TAG])

    @staticmethod
    @router.get(
        "/me",
        response_model=BaseResponse[UserDetailDto],
        summary="본인 정보 조회",
        description="현재 로그인한 사용자 정보 조회",
    )
    async def get_my_info(
            current_user_id: int = Depends(get_current_user_id),
            use_case: UserUseCase = Depends(get_user_use_case),
    ):
        """본인 정보 조회"""
        user = await use_case.get_user(current_user_id)
        return BaseResponse.ok(data=user)

    @staticmethod
    @router.get(
        "/{user_id}",
        response_model=BaseResponse[UserDetailDto],
        summary="사용자 정보 조회",
        description="사용자 정보 조회 (팔로우 통계 포함)",
    )
    async def get_user_info(
            user_id: int,
            current_user_id: int = Depends(get_current_user_id),
            use_case: UserUseCase = Depends(get_user_use_case),
    ):
        """다른 사용자 정보 조회 (팔로우 통계 포함)"""
        user = await use_case.get_user_with_follow_stats(user_id, current_user_id)
        return BaseResponse.ok(data=user)

    @staticmethod
    @router.get(
        "",
        response_model=BaseResponse[PageDto[UserDto]],
        summary="사용자 목록 조회 (type: recommended, followings, followers, blocks)",
        description="사용자 목록 조회 (type: recommended, followings, followers, blocks)",
    )
    async def get_users(
            type: str = Query(
                ...,
                description="사용자 타입: recommended(추천), followings(팔로우하는), followers(팔로워), blocks(차단된)",
                regex="^(recommended|followings|followers|blocks)$",
            ),
            page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
            size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
            current_user_id: int = Depends(get_current_user_id),
            follow_use_case: FollowUseCase = Depends(get_follow_use_case),
            block_user_use_case: BlockUserUseCase = Depends(get_block_user_use_case),
    ):
        """사용자 목록 조회"""
        if type == "recommended":
            users = await follow_use_case.get_recommended_users(
                user_id=current_user_id, page=page, size=size
            )
            message_ko = "추천 유저 목록을 조회했습니다."
            message_en = "Successfully retrieved recommended users."
        elif type == "followings":
            users = await follow_use_case.get_following_list(
                user_id=current_user_id, page=page, size=size
            )
            message_ko = "팔로우 목록을 조회했습니다."
            message_en = "Successfully retrieved following list."
        elif type == "followers":
            users = await follow_use_case.get_followers_list(
                user_id=current_user_id,
                current_user_id=current_user_id,
                page=page,
                size=size,
            )
            message_ko = "팔로워 목록을 조회했습니다."
            message_en = "Successfully retrieved followers list."
        elif type == "blocks":
            users = await block_user_use_case.get_blocked_users(current_user_id, page, size)
            message_ko = "차단된 사용자 목록을 조회했습니다."
            message_en = "Successfully retrieved blocked users list."
        else:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid type. Must be one of: recommended, followings, followers, blocks",
            )

        return BaseResponse.ok(data=users, message_ko=message_ko, message_en=message_en)


class UserRegistRouter:
    router = APIRouter(prefix=UserRouterRootLabel.PREFIX, tags=[UserRouterRootLabel.TAG])

    @staticmethod
    @router.post(
        "",
        summary="사용자 생성 (회원가입)",
        description="사용자 생성 (회원가입)",
        response_model=BaseResponse[UserDetailDto],
    )
    async def create_user(
            user_data: SignUpRequest,
            use_case: UserUseCase = Depends(get_user_use_case),
    ):
        result = await use_case.create_user(
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


class UserUpdateRouter:
    router = APIRouter(prefix=UserRouterRootLabel.PREFIX, tags=[UserRouterRootLabel.TAG])

    @staticmethod
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
            use_case: UserUseCase = Depends(get_user_use_case),
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
        user = await use_case.update_profile(current_user_id, profile_data)
        return BaseResponse.ok(data=user)

    @staticmethod
    @router.put(
        "/fcm-token",
        response_model=BaseResponse[UserDetailDto],
        description="FCM 토큰 업데이트 (토큰 필요)",
    )
    async def update_fcm_token(
            fcm_token: str = Query(..., alias="fcmToken", description="FCM 토큰"),
            current_user_id: int = Depends(get_current_user_id),
            use_case: UserUseCase = Depends(get_user_use_case),
    ):
        user = await use_case.update_fcm_token(current_user_id, fcm_token)

        return BaseResponse.ok(
            data=user,
            message_ko="FCM 토큰이 업데이트되었습니다.",
            message_en="FCM token updated successfully.",
        )

    # - MARK: 약관 동의
    @staticmethod
    @router.post(
        "/terms",
        response_model=BaseResponse[UserDetailDto],
        description="사용자 약관 동의",
    )
    async def accept_terms(
            request: AcceptTermsRequest,
            current_user_id: int = Depends(get_current_user_id),
            use_case: UserUseCase = Depends(get_user_use_case),
    ):
        result = await use_case.accept_terms(current_user_id, request.terms_accepted)
        return BaseResponse.ok(
            data=result,
            message_ko="약관 동의가 완료되었습니다.",
            message_en="Terms accepted successfully.",
            http_status=status.HTTP_200_OK,
        )


class UserDeleteRouter:
    router = APIRouter(prefix=UserRouterRootLabel.PREFIX, tags=[UserRouterRootLabel.TAG])

    @staticmethod
    @router.delete(
        "/me",
        summary="본인 계정 삭제",
        description="현재 로그인한 사용자 삭제",
    )
    async def delete_my_account(
            current_user_id: int = Depends(get_current_user_id),
            use_case: UserUseCase = Depends(get_user_use_case),
    ):
        """본인 계정 삭제"""
        try:
            await use_case.delete_user(current_user_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # 사용자가 존재하지 않는 경우에도 204 No Content 반환
            # (이미 삭제된 상태와 동일하므로)
            if "USER_NOT_FOUND" in str(e):
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            # 다른 오류는 그대로 전파
            raise e


