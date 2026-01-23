"""
랜덤 프로필 이미지 API 엔드포인트
"""

from typing import List

from app.common.schemas import BaseResponse
from app.deps.providers import get_random_profile_image_service
from app.features.users.schemas import RandomProfileImageDto
from app.features.users.services.random_profile_image_service import (
    RandomProfileImageService,
)
from fastapi import APIRouter, Depends, status


class ProfileImageRouter:
    router = APIRouter(prefix="/profile-images", tags=["profile-images"])

    @staticmethod
    @router.get(
        "/random",
        response_model=BaseResponse[RandomProfileImageDto],
        description="랜덤 프로필 이미지 조회",
    )
    async def get_random_profile_image(
            service: RandomProfileImageService = Depends(get_random_profile_image_service),
    ):
        random_image = service.get_random_profile_image()
        return BaseResponse.ok(
            data=random_image,
            message_ko="랜덤 프로필 이미지를 조회했습니다.",
            message_en="Successfully retrieved random profile image.",
            http_status=status.HTTP_200_OK,
        )

    @staticmethod
    @router.get(
        "/all",
        response_model=BaseResponse[List[RandomProfileImageDto]],
        description="모든 프로필 이미지 조회",
    )
    async def get_all_profile_images(
            service: RandomProfileImageService = Depends(get_random_profile_image_service),
    ):
        all_images = service.get_all_profile_images()
        return BaseResponse.ok(
            data=all_images,
            message_ko="모든 프로필 이미지를 조회했습니다.",
            message_en="Successfully retrieved all profile images.",
            http_status=status.HTTP_200_OK,
        )
