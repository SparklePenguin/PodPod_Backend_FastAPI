from typing import Dict, Any, Optional, List
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
from sqlalchemy.orm import selectinload
import json
import os
from datetime import datetime

from app.core.database import get_db
from app.services.artist_schedule_service import ArtistScheduleService
from app.schemas.common import BaseResponse, PageDto
from app.schemas.artist_schedule import (
    ArtistScheduleDto,
    ArtistScheduleCreateRequest,
)
from app.crud.artist_schedule import ArtistScheduleCRUD
from app.crud.artist import ArtistCRUD
from app.core.http_status import HttpStatus

router = APIRouter()


def get_artist_schedule_service(
    db: AsyncSession = Depends(get_db),
) -> ArtistScheduleService:
    return ArtistScheduleService(db)


# - MARK: 아티스트 스케줄 목록 조회
@router.get(
    "",
    response_model=BaseResponse[PageDto[ArtistScheduleDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistScheduleDto]],
            "description": "아티스트 스케줄 목록 조회 성공",
        },
    },
    summary="아티스트 스케줄 목록 조회",
    description="아티스트 스케줄 목록을 조회합니다.",
    tags=["artist-schedules"],
)
async def get_artist_schedules(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    artist_id: Optional[int] = Query(None, description="아티스트 ID 필터"),
    unit_id: Optional[int] = Query(None, description="아티스트 유닛 ID 필터"),
    schedule_type: Optional[int] = Query(None, description="스케줄 유형 필터"),
    artist_schedule_service: ArtistScheduleService = Depends(
        get_artist_schedule_service
    ),
):
    """아티스트 스케줄 목록을 조회합니다."""
    try:
        result = await artist_schedule_service.get_schedules(
            page=page,
            page_size=page_size,
            artist_id=artist_id,
            unit_id=unit_id,
            schedule_type=schedule_type,
        )
        return BaseResponse.ok(result, message_ko="아티스트 스케줄 목록 조회 성공")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"아티스트 스케줄 목록 조회 실패: {str(e)}",
        )


# - MARK: 아티스트 스케줄 상세 조회
@router.get(
    "/{schedule_id}",
    response_model=BaseResponse[ArtistScheduleDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[ArtistScheduleDto],
            "description": "아티스트 스케줄 상세 조회 성공",
        },
        HttpStatus.NOT_FOUND: {
            "description": "아티스트 스케줄을 찾을 수 없음",
        },
    },
    summary="아티스트 스케줄 상세 조회",
    description="특정 아티스트 스케줄의 상세 정보를 조회합니다.",
    tags=["artist-schedules"],
)
async def get_artist_schedule(
    schedule_id: int = Path(..., description="스케줄 ID"),
    artist_schedule_service: ArtistScheduleService = Depends(
        get_artist_schedule_service
    ),
):
    """아티스트 스케줄 상세 정보를 조회합니다."""
    try:
        schedule = await artist_schedule_service.get_schedule_by_id(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="아티스트 스케줄을 찾을 수 없습니다.",
            )
        return BaseResponse.ok(schedule, message_ko="아티스트 스케줄 상세 조회 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"아티스트 스케줄 상세 조회 실패: {str(e)}",
        )


# - MARK: JSON 파일에서 아티스트 스케줄 데이터 가져오기 (Internal)
@router.post(
    "/import-from-json",
    response_model=BaseResponse[Dict[str, Any]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[Dict[str, Any]],
            "description": "JSON 파일에서 아티스트 스케줄 데이터 가져오기 성공",
        },
    },
    summary="JSON 파일에서 아티스트 스케줄 데이터 가져오기",
    description="kpop_schedule_2025.json 파일에서 아티스트 스케줄 데이터를 읽어와서 데이터베이스에 저장합니다.",
    tags=["internal"],
)
async def import_artist_schedules_from_json(
    artist_schedule_service: ArtistScheduleService = Depends(
        get_artist_schedule_service
    ),
):
    """JSON 파일에서 아티스트 스케줄 데이터를 가져와서 저장합니다."""
    try:
        # JSON 파일 경로
        json_file_path = os.path.join(
            os.path.dirname(__file__), "../../../../mvp/kpop_schedule_2025.json"
        )

        if not os.path.exists(json_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="kpop_schedule_2025.json 파일을 찾을 수 없습니다.",
            )

        # JSON 파일 읽기
        with open(json_file_path, "r", encoding="utf-8") as file:
            schedule_data = json.load(file)

        # 데이터 가져오기 실행
        result = await artist_schedule_service.import_schedules_from_json(schedule_data)

        print(f"Import result: {result}")

        return BaseResponse.ok(
            result, message_ko="JSON 파일에서 아티스트 스케줄 데이터 가져오기 성공"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"JSON 파일에서 아티스트 스케줄 데이터 가져오기 실패: {str(e)}",
        )
