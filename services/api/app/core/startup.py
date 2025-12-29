"""
애플리케이션 시작 시 실행되는 초기화 함수들
"""

import asyncio
import os

from app.core.config import settings
from app.core.error_codes import (
    load_error_codes_from_file,
    load_error_codes_from_sheets,
)


async def initialize_error_codes():
    """에러 코드를 초기화합니다."""
    print("에러 코드 초기화 중...")

    # 1. Google Sheets에서 로드 시도
    if settings.GOOGLE_SHEETS_ID:
        print(f"Google Sheets에서 에러 코드 로드 시도: {settings.GOOGLE_SHEETS_ID}")
        success = await load_error_codes_from_sheets(
            spreadsheet_id=settings.GOOGLE_SHEETS_ID,
            range_name=settings.GOOGLE_SHEETS_RANGE,
        )

        if success:
            print("Google Sheets에서 에러 코드 로드 성공")
            return
        else:
            print("Google Sheets 로드 실패, 백업 파일 시도")

    # 2. 백업 파일에서 로드 시도
    backup_file = "error_codes_backup.json"
    if os.path.exists(backup_file):
        print(f"백업 파일에서 에러 코드 로드 시도: {backup_file}")
        success = load_error_codes_from_file(backup_file)

        if success:
            print("백업 파일에서 에러 코드 로드 성공")
            return
        else:
            print("백업 파일 로드 실패")

    # 3. 에러 코드 로드 실패
    print("에러 코드 로드에 실패했습니다. 서버는 에러 코드 없이 시작됩니다.")
    print("Google Sheets 설정을 확인하거나 백업 파일을 생성해주세요.")


async def startup_events():
    """애플리케이션 시작 시 실행되는 이벤트들"""
    print("애플리케이션 시작 이벤트 실행 중...")

    # 에러 코드 초기화
    await initialize_error_codes()

    # 스케줄러 시작
    from app.core.services.scheduler_service import start_scheduler

    asyncio.create_task(start_scheduler())
    print("스케줄러 시작됨:")
    print("- 매일 아침 10시: 리뷰 유도 알림")
    print("- 5분마다: 파티 시작 임박 알림")
    print("- 1시간마다: 마감 임박 알림")

    print("애플리케이션 시작 이벤트 완료")


def sync_startup_events():
    """동기적으로 실행되는 시작 이벤트들"""
    print("동기 시작 이벤트 실행 중...")

    # 필요한 디렉토리 생성 (settings에서 설정된 경로 사용)
    from pathlib import Path

    if settings.UPLOADS_DIR:
        uploads_dir = Path(settings.UPLOADS_DIR)
        (uploads_dir / "pods" / "images").mkdir(parents=True, exist_ok=True)
        (uploads_dir / "pods" / "thumbnails").mkdir(parents=True, exist_ok=True)
        (uploads_dir / "users" / "profiles").mkdir(parents=True, exist_ok=True)
        (uploads_dir / "artists").mkdir(parents=True, exist_ok=True)

    if settings.LOGS_DIR:
        Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)

    print("동기 시작 이벤트 완료")
