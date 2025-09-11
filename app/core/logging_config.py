import logging
import sys
import json
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Dict, Any

# 로그 디렉토리 생성
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 환경별 로그 레벨 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# 구조화된 로그 포맷터
class JSONFormatter(logging.Formatter):
    """JSON 형태로 로그를 포맷하는 클래스"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 추가 컨텍스트 정보가 있으면 포함
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "endpoint"):
            log_entry["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration"):
            log_entry["duration"] = record.duration

        # 예외 정보가 있으면 포함
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


# 일반 텍스트 포맷터 (개발용)
text_format = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def setup_logging():
    """개선된 로깅 설정"""
    # 기존 핸들러 제거 (중복 방지)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(getattr(logging, LOG_LEVEL))

    # 콘솔 핸들러 (개발용 - 텍스트 포맷)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(text_format)

    # 애플리케이션 로그 파일 핸들러 (JSON 포맷)
    app_handler = TimedRotatingFileHandler(
        log_dir / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,  # 30일 보관
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(JSONFormatter())

    # 에러 로그 파일 핸들러 (JSON 포맷)
    error_handler = TimedRotatingFileHandler(
        log_dir / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,  # 30일 보관
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())

    # API 요청 로그 파일 핸들러 (JSON 포맷)
    api_handler = TimedRotatingFileHandler(
        log_dir / "api.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(JSONFormatter())

    # 핸들러 추가
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(api_handler)

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # 액세스 로그 줄이기
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pymysql").setLevel(logging.WARNING)

    # 애플리케이션 로거 설정
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)

    # API 로거 설정
    api_logger = logging.getLogger("app.api")
    api_logger.setLevel(logging.INFO)

    logging.info(
        "로깅 시스템이 초기화되었습니다.",
        extra={"log_level": LOG_LEVEL, "log_dir": str(log_dir)},
    )


def get_logger(name: str) -> logging.Logger:
    """구조화된 로거를 반환"""
    return logging.getLogger(f"app.{name}")


def log_api_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    user_id: str = None,
    request_id: str = None,
):
    """API 요청 로그를 기록"""
    logger.info(
        f"API 요청: {method} {endpoint}",
        extra={
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration": duration,
            "user_id": user_id,
            "request_id": request_id,
        },
    )


def log_user_action(
    logger: logging.Logger, action: str, user_id: str, details: Dict[str, Any] = None
):
    """사용자 액션 로그를 기록"""
    extra = {"user_id": user_id, "action": action}
    if details:
        extra.update(details)

    logger.info(f"사용자 액션: {action}", extra=extra)


def log_database_operation(
    logger: logging.Logger, operation: str, table: str, duration: float = None
):
    """데이터베이스 작업 로그를 기록"""
    extra = {"operation": operation, "table": table}
    if duration:
        extra["duration"] = duration

    logger.info(f"DB 작업: {operation} on {table}", extra=extra)
