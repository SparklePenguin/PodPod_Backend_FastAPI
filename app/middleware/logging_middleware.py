"""
API 요청/응답 로깅 미들웨어
"""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger

logger = get_logger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """API 요청/응답을 로깅하는 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        # 요청 시작 시간
        start_time = time.time()
        
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        # 요청 정보 로깅
        logger.info(
            f"요청 시작: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "endpoint": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # 응답 처리
        try:
            response = await call_next(request)
            
            # 응답 시간 계산
            duration = time.time() - start_time
            
            # 응답 정보 로깅
            logger.info(
                f"요청 완료: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                    "response_size": response.headers.get("content-length"),
                }
            )
            
            # 응답 헤더에 요청 ID 추가
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # 에러 발생 시 로깅
            duration = time.time() - start_time
            
            logger.error(
                f"요청 실패: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "endpoint": request.url.path,
                    "duration": duration,
                    "error": str(e),
                },
                exc_info=True
            )
            
            raise
