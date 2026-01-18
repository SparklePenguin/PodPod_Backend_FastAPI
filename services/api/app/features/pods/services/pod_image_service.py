"""Pod Image Service - 파티 이미지 처리

파티 썸네일 생성, 이미지 삭제 등 이미지 관련 작업을 담당합니다.
"""

import io
import uuid
from pathlib import Path

from fastapi import UploadFile
from PIL import Image

from app.core.config import settings
from app.features.pods.exceptions import InvalidImageException
from app.features.pods.repositories.pod_repository import PodRepository


class PodImageService:
    """파티 이미지 처리 서비스"""

    def __init__(self, pod_repo: PodRepository):
        self._pod_repo = pod_repo

    async def create_thumbnail_from_image(self, image: UploadFile) -> str:
        """이미지에서 썸네일을 생성하여 저장"""
        # 이미지 읽기
        image_content = await image.read()

        # 파일 포인터를 다시 처음으로 되돌리기 (다른 곳에서 재사용 가능하도록)
        await image.seek(0)

        # 이미지 파일 검증
        if not image_content:
            raise InvalidImageException("이미지 파일이 비어있습니다")

        try:
            img = Image.open(io.BytesIO(image_content))

            # EXIF 회전 정보 처리
            try:
                ORIENTATION = 274  # EXIF orientation tag number

                # PIL.Image의 getexif() 메서드 사용 (Pillow 6.0+)
                exif = (
                    img.getexif()
                    if hasattr(img, "getexif")
                    else getattr(img, "_getexif", lambda: None)()
                )
                if exif is not None:
                    orientation = exif.get(ORIENTATION)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, TypeError):
                # EXIF 데이터가 없거나 처리할 수 없는 경우 무시
                pass

        except Exception as e:
            raise InvalidImageException(f"이미지 파일을 읽을 수 없습니다: {str(e)}")

        # 썸네일 크기 (300x300)
        thumbnail_size = (300, 300)

        # 썸네일 생성 (비율 유지하며 리사이즈)
        img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

        # 썸네일 저장
        thumbnail_filename = f"{uuid.uuid4()}.jpg"

        # 파일시스템 경로 (실제 저장 위치)
        thumbnails_dir = Path(settings.UPLOADS_DIR) / "pods" / "thumbnails"
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_fs_path = thumbnails_dir / thumbnail_filename

        # RGB로 변환 (JPEG 저장을 위해)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 썸네일 저장
        img.save(str(thumbnail_fs_path), "JPEG", quality=85, optimize=True)

        # URL 경로 반환
        thumbnail_url = f"/uploads/pods/thumbnails/{thumbnail_filename}"
        return thumbnail_url

    async def delete_pod_images(self, pod_id: int) -> None:
        """파티의 모든 이미지 삭제 (PodDetail의 images 삭제)"""
        await self._pod_repo.delete_pod_images(pod_id)
