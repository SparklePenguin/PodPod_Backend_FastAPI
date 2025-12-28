"""
랜덤 프로필 이미지 API 엔드포인트
"""

from typing import List

from fastapi import APIRouter, Depends

from app.common.schemas import BaseResponse
from app.core.http_status import HttpStatus
from app.features.users.services.random_profile_image_service import (
    RandomProfileImageService,
)
from app.features.users.schemas.random_profile_image import RandomProfileImageResponse

router = APIRouter()


def get_random_profile_image_service() -> RandomProfileImageService:
    """랜덤 프로필 이미지 서비스 의존성 주입"""
    return RandomProfileImageService()


@router.get(
    "/random",
    response_model=BaseResponse[RandomProfileImageResponse],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[RandomProfileImageResponse],
            "description": "랜덤 프로필 이미지 조회 성공",
        },
    },
    summary="랜덤 프로필 이미지 조회",
    description="사용 가능한 프로필 이미지 중에서 랜덤으로 하나를 선택하여 반환합니다.",
    tags=["profile-images"],
)
async def get_random_profile_image(
    service: RandomProfileImageService = Depends(get_random_profile_image_service),
):
    """랜덤 프로필 이미지 조회"""
    random_image = service.get_random_profile_image()

    return BaseResponse.ok(
        data=random_image,
        message_ko="랜덤 프로필 이미지를 조회했습니다.",
        message_en="Successfully retrieved random profile image.",
        http_status=HttpStatus.OK,
    )


@router.get(
    "/all",
    response_model=BaseResponse[List[RandomProfileImageResponse]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[List[RandomProfileImageResponse]],
            "description": "모든 프로필 이미지 조회 성공",
        },
    },
    summary="모든 프로필 이미지 조회",
    description="사용 가능한 모든 프로필 이미지 목록을 반환합니다.",
    tags=["profile-images"],
)
async def get_all_profile_images(
    service: RandomProfileImageService = Depends(get_random_profile_image_service),
):
    """모든 프로필 이미지 조회"""
    all_images = service.get_all_profile_images()

    return BaseResponse.ok(
        data=all_images,
        message_ko="모든 프로필 이미지를 조회했습니다.",
        message_en="Successfully retrieved all profile images.",
        http_status=HttpStatus.OK,
    )
