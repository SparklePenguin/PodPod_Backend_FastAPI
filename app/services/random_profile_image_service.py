"""
랜덤 프로필 이미지 서비스
"""

import os
import random
from typing import List
from app.schemas.random_profile_image import RandomProfileImageDto


class RandomProfileImageService:
    """랜덤 프로필 이미지 서비스"""

    def __init__(self):
        self.images_dir = "UserImages"
        self.supported_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]

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

    def get_random_profile_image(self) -> RandomProfileImageDto:
        """랜덤 프로필 이미지를 반환"""
        available_images = self.get_available_images()

        if not available_images:
            # 기본 이미지가 없으면 빈 문자열 반환
            return RandomProfileImageDto(image_url="", image_name="")

        # 랜덤으로 이미지 선택
        selected_image = random.choice(available_images)

        # 이미지 URL 생성 (정적 파일 서빙을 위해)
        image_url = f"/static/UserImages/{selected_image}"

        return RandomProfileImageDto(image_url=image_url, image_name=selected_image)

    def get_all_profile_images(self) -> List[RandomProfileImageDto]:
        """모든 프로필 이미지 목록을 반환"""
        available_images = self.get_available_images()

        images = []
        for image_name in available_images:
            image_url = f"/static/UserImages/{image_name}"
            images.append(
                RandomProfileImageDto(image_url=image_url, image_name=image_name)
            )

        return images
