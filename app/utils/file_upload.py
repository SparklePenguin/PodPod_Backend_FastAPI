import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from typing import Optional


async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """파일을 서버에 저장하고 파일 경로를 반환"""
    try:
        # 파일 확장자 추출
        file_extension = (
            Path(upload_file.filename).suffix if upload_file.filename else ""
        )

        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # 업로드 디렉토리 생성
        upload_dir = Path(destination)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 파일 저장 경로
        file_path = upload_dir / unique_filename

        # 파일 저장
        with open(file_path, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)

        # 파일 포인터를 다시 처음으로 되돌리기 (다른 곳에서 재사용 가능하도록)
        await upload_file.seek(0)

        # 파일 URL 반환 (상대 경로) - destination 경로를 포함
        return f"/{destination}/{unique_filename}"

    except Exception as e:
        raise Exception(f"파일 업로드 실패: {str(e)}")


async def delete_upload_file(file_path: str) -> bool:
    """업로드된 파일 삭제"""
    try:
        if file_path and file_path.startswith("/uploads/"):
            # 상대 경로를 절대 경로로 변환
            absolute_path = Path(".") / file_path.lstrip("/")
            if absolute_path.exists():
                absolute_path.unlink()
                return True
        return False
    except Exception as e:
        print(f"파일 삭제 실패: {str(e)}")
        return False


def is_valid_image_file(file: UploadFile) -> bool:
    """이미지 파일인지 검증"""
    import logging

    logger = logging.getLogger(__name__)

    # 파일명과 content_type 로깅
    logger.info(
        f"파일 검증: filename={file.filename}, content_type={file.content_type}"
    )

    # 파일명이 없으면 False
    if not file.filename:
        logger.warning("파일명이 없습니다")
        return False

    # 파일 확장자 검증
    file_extension = Path(file.filename).suffix.lower()
    valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    if file_extension not in valid_extensions:
        logger.warning(f"지원하지 않는 파일 확장자: {file_extension}")
        return False

    # content_type이 있으면 검증
    if file.content_type:
        valid_image_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
            "application/octet-stream",  # 바이너리 파일 (확장자로 추가 검증)
        ]

        if file.content_type not in valid_image_types:
            logger.warning(f"지원하지 않는 content_type: {file.content_type}")
            return False

    logger.info("이미지 파일 검증 통과")
    return True


async def upload_profile_image(image: UploadFile) -> Optional[str]:
    """프로필 이미지 업로드"""
    if not image:
        return None

    # 이미지 파일 검증
    if not is_valid_image_file(image):
        error_msg = f"유효하지 않은 이미지 파일입니다. 파일명: {image.filename}, Content-Type: {image.content_type}"
        raise ValueError(error_msg)

    # 파일 크기 검증 (5MB 제한)
    content = await image.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB
        raise ValueError("이미지 파일 크기는 5MB를 초과할 수 없습니다")

    # 파일 포인터를 다시 처음으로
    await image.seek(0)

    # 파일 저장
    return await save_upload_file(image, "uploads/profile_images")


def is_animatable_image(filename: str) -> bool:
    """이미지가 애니메이션 가능한지 확인 (GIF, WebP 등)"""
    if not filename:
        return False

    extension = Path(filename).suffix.lower()
    animatable_extensions = [".gif", ".webp", ".apng"]
    return extension in animatable_extensions


def get_file_size_string(size_bytes: int) -> str:
    """파일 크기를 문자열로 변환"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


async def upload_artist_image(image: UploadFile) -> dict:
    """아티스트 이미지 업로드 및 메타데이터 분석"""
    if not image:
        raise ValueError("이미지 파일이 필요합니다")

    # 이미지 파일 검증
    if not is_valid_image_file(image):
        raise ValueError("유효하지 않은 이미지 파일입니다")

    # 파일 크기 검증 (10MB 제한)
    content = await image.read()
    file_size = len(content)
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise ValueError("이미지 파일 크기는 10MB를 초과할 수 없습니다")

    # 파일 포인터를 다시 처음으로
    await image.seek(0)

    # 파일 저장
    file_path = await save_upload_file(image, "uploads/artists")

    # 파일 ID 생성 (UUID)
    file_id = str(uuid.uuid4())

    # 메타데이터 분석
    is_animatable = is_animatable_image(image.filename)
    size_string = get_file_size_string(file_size)

    return {
        "path": file_path,
        "file_id": file_id,
        "is_animatable": is_animatable,
        "size": size_string,
    }
