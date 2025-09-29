from typing import Dict, Any, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path,
    File,
    UploadFile,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.artist_service import ArtistService
from app.schemas.common import BaseResponse, PageDto
from app.schemas.artist import ArtistDto, ArtistSimpleDto
from app.schemas.artist_image import (
    ArtistImageDto,
    UpdateArtistImageRequest,
)
from app.crud.artist import ArtistCRUD
from app.core.http_status import HttpStatus

router = APIRouter()


def get_artist_service(db: AsyncSession = Depends(get_db)) -> ArtistService:
    return ArtistService(db)


# - MARK: 아티스트 목록 조회 (간소화)
@router.get(
    "/simple",
    response_model=BaseResponse[PageDto[ArtistSimpleDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistSimpleDto]],
            "description": "아티스트 목록 조회 성공 (간소화)",
        },
    },
    summary="아티스트 목록 조회 (간소화)",
    description="아티스트 목록을 간소화된 형태로 조회합니다. ArtistUnit의 artist_id에 해당하는 아티스트 정보(unitId, artistId, 이름)를 반환합니다.",
)
async def get_artists_simple(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    is_active: bool = Query(True, description="활성화 상태 필터 (true/false)"),
    artist_service: ArtistService = Depends(get_artist_service),
):
    """아티스트 목록 조회 (간소화 - ArtistUnit의 artist_id에 해당하는 아티스트 정보)"""
    page_data = await artist_service.get_artists_simple(
        page=page, page_size=page_size, is_active=is_active
    )
    return BaseResponse.ok(data=page_data)


# - MARK: 아티스트 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[PageDto[ArtistDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistDto]],
            "description": "아티스트 목록 조회 성공",
        },
    },
    summary="아티스트 목록 조회",
    description="아티스트 목록을 페이지네이션과 필터링으로 조회합니다. 기본적으로 활성화된 아티스트만 반환합니다.",
)
async def get_artists(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    is_active: bool = Query(True, description="활성화 상태 필터 (true/false)"),
    artist_service: ArtistService = Depends(get_artist_service),
):
    """아티스트 목록 조회 (페이지네이션 및 is_active 필터링 지원)"""
    page_data = await artist_service.get_artists(
        page=page, page_size=page_size, is_active=is_active
    )
    return BaseResponse.ok(data=page_data)


# - MARK: 특정 아티스트 조회
@router.get(
    "/{artist_id}",
    response_model=BaseResponse[PageDto[ArtistDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistDto]],
            "description": "아티스트 조회 성공",
        },
    },
    summary="특정 아티스트 조회",
    description="ID로 특정 아티스트의 상세 정보를 조회합니다. 이미지, 멤버, 다국어 이름 등 모든 관련 데이터를 포함합니다.",
)
async def get_artist(
    artist_id: int,
    artist_service: ArtistService = Depends(get_artist_service),
):
    """특정 아티스트 조회"""
    artist = await artist_service.get_artist(artist_id)
    if not artist:
        return BaseResponse.error(
            error_key="ARTIST_NOT_FOUND",
            error_code=4006,
            http_status=HttpStatus.NOT_FOUND,
            message_ko="아티스트를 찾을 수 없습니다.",
            message_en="Artist not found.",
        )
    return BaseResponse.ok(data=artist)


# - MARK: MVP 아티스트 생성 (내부용)
@router.post(
    "/mvp",
    response_model=BaseResponse[dict],
    responses={
        200: {"model": BaseResponse[dict], "description": "BLIP+MVP 동기화 성공"},
    },
    tags=["internal"],
    summary="MVP 아티스트 생성 (내부용)",
    description="⚠️ 내부용 API - BLIP 전체 데이터와 MVP 목록을 병합하여 동기화합니다.",
)
async def sync_mvp_artists(
    artist_service: ArtistService = Depends(get_artist_service),
):
    """BLIP+MVP 병합 동기화 (내부용)"""
    result = await artist_service.sync_blip_and_mvp()
    return BaseResponse.ok(data=result)


@router.get(
    "/{artistId}/images",
    response_model=BaseResponse[list[ArtistImageDto]],
    tags=["internal"],
    summary="아티스트 이미지 목록 조회",
    description="⚠️ 내부용 API - 특정 아티스트의 모든 이미지를 조회합니다.",
)
async def get_artist_images(
    artist_id: int = Path(..., description="아티스트 ID", alias="artistId"),
    db: AsyncSession = Depends(get_db),
):
    """아티스트의 모든 이미지를 조회합니다."""
    try:
        artist_crud = ArtistCRUD(db)

        # 아티스트 조회 (이미지 포함)
        artist = await artist_crud.get_by_id(artist_id)

        if not artist:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"아티스트를 찾을 수 없습니다. ID: {artist_id}",
            )

        # 이미지 데이터를 DTO로 변환
        images = [ArtistImageDto.model_validate(image) for image in artist.images]

        return BaseResponse.ok(
            data=images,
            http_status=HttpStatus.OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"아티스트 이미지 조회 실패: {str(e)}",
        )


@router.post(
    "/{artistId}/images",
    response_model=BaseResponse[Dict[str, Any]],
    tags=["internal"],
    summary="아티스트 이미지 생성",
    description="⚠️ 내부용 API - 특정 아티스트에 새로운 이미지를 생성합니다. 이미지 파일 업로드 지원.",
)
async def create_artist_image(
    artist_id: int = Path(..., description="아티스트 ID", alias="artistId"),
    # Form 파라미터 (alias 작동 안함):
    image: Optional[UploadFile] = File(None, description="이미지 파일"),
    path: Optional[str] = Form(None, description="이미지 경로"),
    fileId: Optional[str] = Form(None, description="파일 ID"),
    isAnimatable: bool = Form(False, description="애니메이션 가능 여부"),
    size: Optional[str] = Form(None, description="이미지 크기"),
    db: AsyncSession = Depends(get_db),
):
    """아티스트에 새로운 이미지를 생성합니다. 이미지 파일 또는 폼 데이터로 생성 가능합니다."""
    try:
        artist_crud = ArtistCRUD(db)
        image_data = {}

        # 이미지 파일이 제공된 경우
        if image:
            from app.utils.file_upload import upload_artist_image

            try:
                upload_result = await upload_artist_image(image)
                image_data.update(upload_result)
            except ValueError as e:
                raise HTTPException(
                    status_code=HttpStatus.BAD_REQUEST,
                    detail=str(e),
                )
            except Exception as e:
                raise HTTPException(
                    status_code=HttpStatus.INTERNAL_SERVER_ERROR,
                    detail=f"이미지 업로드 실패: {str(e)}",
                )

        # 폼 데이터가 제공된 경우 (빈 문자열은 제외)
        # file_id는 Form에서 제공된 경우에만 덮어쓰기 (기존 이미지 찾기용)
        print(
            f"DEBUG: Form 데이터 - path: '{path}', fileId: '{fileId}', isAnimatable: {isAnimatable}, size: '{size}'"
        )
        form_data = {}
        if path is not None and path.strip():
            form_data["path"] = path
        if fileId is not None:
            form_data["file_id"] = fileId
            print(f"DEBUG: Form fileId 추가됨: {fileId}")
        if isAnimatable is not None:
            form_data["is_animatable"] = isAnimatable
        if size is not None and size.strip():
            form_data["size"] = size

        if form_data:
            print(f"DEBUG: Form 데이터로 업데이트: {form_data}")
            image_data.update(form_data)

        print(f"DEBUG: 최종 image_data: {image_data}")

        if not image_data:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="생성할 데이터가 없습니다. 이미지 파일 또는 폼 데이터를 제공해주세요.",
            )

        success, message, created_image = await artist_crud.create_artist_image(
            artist_id, image_data
        )

        if not success:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail=message,
            )

        return BaseResponse.ok(
            data={
                "message": message,
                "artist_id": artist_id,
                "image_id": created_image.id,
                "created_data": image_data,
            },
            http_status=HttpStatus.CREATED,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"아티스트 이미지 생성 실패: {str(e)}",
        )
