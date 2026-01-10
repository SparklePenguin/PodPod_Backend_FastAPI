"""
애플리케이션 시작 시 실행되는 초기화 함수들
"""

import asyncio

from app.core.config import settings


async def startup_events():
    """애플리케이션 시작 시 실행되는 이벤트들"""
    print("애플리케이션 시작 이벤트 실행 중...")

    # WebSocketService에 Redis 설정
    await initialize_websocket_redis()

    # 스케줄러 시작
    from app.core.services.scheduler_service import start_scheduler

    asyncio.create_task(start_scheduler())
    print("스케줄러 시작됨:")
    print("- 매일 아침 10시: 리뷰 유도 알림")
    print("- 5분마다: 파티 시작 임박 알림")
    print("- 1시간마다: 마감 임박 알림")

    print("애플리케이션 시작 이벤트 완료")


async def initialize_websocket_redis():
    """WebSocketService 싱글톤에 Redis 설정"""
    try:
        from app.core.config import settings
        from app.deps.redis import get_redis_client

        if settings.USE_WEBSOCKET_CHAT:
            from app.core.container import container

            websocket_service = container.websocket_service()
            if websocket_service:
                redis = await get_redis_client()
                websocket_service.set_redis(redis)
                print("WebSocketService에 Redis 설정 완료")
    except Exception as e:
        print(f"WebSocketService Redis 설정 실패 (무시됨): {e}")


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
