import sys
from pathlib import Path as PathLib
from typing import Any, Dict, Optional

# 프로젝트 루트를 Python path에 추가 (메인 API의 app 모듈 접근용)
project_root = PathLib(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from shared.utils.file_upload import upload_artist_image

from app.repositories.artist_repository import ArtistRepository
from app.services.artist_service import ArtistService

router = APIRouter(prefix="/artists", tags=["artists-scraping"])


@router.post(
    "/images/{artist_id}",
    summary="아티스트 이미지 생성",
)
async def create_artist_image(
    artist_id: int = Path(..., description="아티스트 ID"),
    image: Optional[UploadFile] = File(None, description="이미지 파일"),
    path: Optional[str] = Form(None, description="이미지 경로"),
    file_id: Optional[str] = Form(None, description="파일 ID"),
    is_animatable: bool = Form(False, description="애니메이션 가능 여부"),
    size: Optional[str] = Form(None, description="이미지 크기"),
    db: AsyncSession = Depends(get_session),
):
    """아티스트에 새로운 이미지를 생성합니다."""
    try:
        artist_crud = ArtistRepository(db)
        image_data = {}

        # 이미지 파일이 제공된 경우
        if image:
            try:
                upload_result = await upload_artist_image(image)
                image_data.update(upload_result)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"이미지 업로드 실패: {str(e)}"
                )

        # 폼 데이터가 제공된 경우
        form_data = {}
        if path is not None and path.strip():
            form_data["path"] = path
        if file_id is not None:
            form_data["file_id"] = file_id
        if is_animatable is not None:
            form_data["is_animatable"] = is_animatable
        if size is not None and size.strip():
            form_data["size"] = size

        if form_data:
            image_data.update(form_data)

        if not image_data:
            raise HTTPException(
                status_code=400,
                detail="생성할 데이터가 없습니다.",
            )

        success, message, created_image = await artist_crud.create_artist_image(
            artist_id, image_data
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        if created_image is None:
            raise HTTPException(status_code=500, detail="이미지 생성에 실패했습니다.")

        image_id = getattr(created_image, "id", None)
        if image_id is None:
            raise HTTPException(
                status_code=500, detail="생성된 이미지 ID를 가져올 수 없습니다."
            )

        return {
            "message": message,
            "artist_id": artist_id,
            "image_id": image_id,
            "created_data": image_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"아티스트 이미지 생성 실패: {str(e)}"
        )


@router.post(
    "/mvp",
    summary="MVP 아티스트 생성 (내부용)",
    description="⚠️ 내부용 API - BLIP 전체 데이터와 MVP 목록을 병합하여 동기화합니다.",
)
async def sync_mvp_artists(
    session: AsyncSession = Depends(get_session),
):
    """BLIP+MVP 병합 동기화 (내부용)"""
    service = ArtistService(session)
    result = await service.sync_blip_and_mvp()
    return result
