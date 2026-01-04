"""
랜덤 프로필 이미지 서비스
"""

import os
import random
from pathlib import Path
from typing import List

from app.core.config import settings
from app.features.users.schemas.random_profile_image import RandomProfileImageDto


class RandomProfileImageService:
    """랜덤 프로필 이미지 서비스"""

    def __init__(self):
        # 환경별 uploads 디렉토리의 profile_random_images 사용
        uploads_dir = Path(settings.UPLOADS_DIR)
        self.images_dir = str(uploads_dir / "profile_random_images")
        self.supported_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]

    # - MARK: 사용 가능한 이미지 목록 조회
    def get_available_images(self) -> List[str]:
        """사용 가능한 이미지 파일 목록을 반환"""
        try:
            if not os.path.exists(self.images_dir):
                return []

            images = []
            for filename in os.listdir(self.images_dir):
                if any(
                    filename.lower().endswith(ext) for ext in self.supported_extensions
                ):
                    images.append(filename)

            return sorted(images)
        except Exception:
            return []

    # - MARK: 랜덤 프로필 이미지 조회
    def get_random_profile_image(self) -> RandomProfileImageDto:
        """랜덤 프로필 이미지를 반환"""
        available_images = self.get_available_images()

        if not available_images:
            # 기본 이미지가 없으면 빈 문자열 반환
            return RandomProfileImageDto(image_url="", image_name="")

        # 랜덤으로 이미지 선택
        selected_image = random.choice(available_images)

        # 이미지 URL 생성 (프론트엔드에서 환경별로 처리)
        image_url = f"/uploads/profile_random_images/{selected_image}"

        return RandomProfileImageDto(image_url=image_url, image_name=selected_image)

    # - MARK: 모든 프로필 이미지 목록 조회
    def get_all_profile_images(self) -> List[RandomProfileImageDto]:
        """모든 프로필 이미지 목록을 반환"""
        available_images = self.get_available_images()

        images = []
        for image_name in available_images:
            # 이미지 URL 생성 (프론트엔드에서 환경별로 처리)
            image_url = f"/uploads/profile_random_images/{image_name}"

            images.append(
                RandomProfileImageDto(image_url=image_url, image_name=image_name)
            )

        return images
