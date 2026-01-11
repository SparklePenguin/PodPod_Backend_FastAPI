import gzip
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict

# 환경별 로그 레벨 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 로그 디렉토리는 config에서 가져옴 (환경별로 분리)
try:
    from app.core.config import settings

    log_dir = Path(settings.LOGS_DIR) if settings.LOGS_DIR else Path("logs")
except ImportError:
    # config가 아직 로드되지 않은 경우 기본값 사용
    log_dir = Path("logs")

# 로그 디렉토리 생성
log_dir.mkdir(parents=True, exist_ok=True)


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

        # 추가 컨텍스트 정보가 있으면 포함 (getattr로 안전하게 접근)
        user_id = getattr(record, "user_id", None)
        if user_id is not None:
            log_entry["user_id"] = user_id

        request_id = getattr(record, "request_id", None)
        if request_id is not None:
            log_entry["request_id"] = request_id

        endpoint = getattr(record, "endpoint", None)
        if endpoint is not None:
            log_entry["endpoint"] = endpoint

        method = getattr(record, "method", None)
        if method is not None:
            log_entry["method"] = method

        status_code = getattr(record, "status_code", None)
        if status_code is not None:
            log_entry["status_code"] = status_code

        duration = getattr(record, "duration", None)
        if duration is not None:
            log_entry["duration"] = duration

        headers = getattr(record, "headers", None)
        if headers is not None:
            log_entry["headers"] = headers

        request_body = getattr(record, "request_body", None)
        if request_body is not None:
            log_entry["request_body"] = request_body

        query_params = getattr(record, "query_params", None)
        if query_params is not None:
            log_entry["query_params"] = query_params

        client_ip = getattr(record, "client_ip", None)
        if client_ip is not None:
            log_entry["client_ip"] = client_ip

        user_agent = getattr(record, "user_agent", None)
        if user_agent is not None:
            log_entry["user_agent"] = user_agent

        # 예외 정보가 있으면 포함
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


# 일반 텍스트 포맷터 (개발용)
text_format = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# 압축 기능이 있는 TimedRotatingFileHandler
class CompressedTimedRotatingFileHandler(TimedRotatingFileHandler):
    """로그 파일을 자동으로 압축하는 TimedRotatingFileHandler"""

    def doRollover(self):
        """로테이션 시 기존 파일을 압축"""
        super().doRollover()
        # 로테이션된 파일 압축
        self._compress_old_logs()

    def _compress_old_logs(self):
        """오래된 로그 파일들을 압축"""
        base_path = Path(self.baseFilename)
        log_dir = base_path.parent

        # 같은 디렉토리의 .log 파일들을 찾아서 압축
        for log_file in log_dir.glob(f"{base_path.stem}.*.log"):
            if log_file.suffix == ".log" and not log_file.name.endswith(".gz"):
                gz_file = log_file.with_suffix(".log.gz")
                try:
                    with open(log_file, "rb") as f_in:
                        with gzip.open(gz_file, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    log_file.unlink()  # 원본 파일 삭제
                except Exception as e:
                    # 압축 실패해도 계속 진행
                    logging.warning(f"로그 파일 압축 실패: {log_file}, 오류: {e}")


def setup_logging():
    """개선된 로깅 설정"""
    # 기존 핸들러 제거 (중복 방지)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(getattr(logging, LOG_LEVEL))

    # 콘솔 핸들러 (개발용 - 텍스트 포맷)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # DEBUG 레벨로 변경
    console_handler.setFormatter(text_format)

    # 애플리케이션 로그 파일 핸들러 (JSON 포맷)
    # 시간 기반 로테이션: 매일 자정, 자동 압축
    app_handler = CompressedTimedRotatingFileHandler(
        log_dir / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,  # 30일 보관
        encoding="utf-8",
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(JSONFormatter())

    # 에러 로그 파일 핸들러 (JSON 포맷)
    # 에러 로그는 더 오래 보관
    error_handler = CompressedTimedRotatingFileHandler(
        log_dir / "error.log",
        when="midnight",
        interval=1,
        backupCount=90,  # 에러 로그는 90일 보관 (더 오래 보관)
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())

    # API 요청 로그 파일 핸들러 (JSON 포맷)
    api_handler = CompressedTimedRotatingFileHandler(
        log_dir / "api.log",
        when="midnight",
        interval=1,
        backupCount=30,  # 30일 보관
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
    user_id: str | None = None,
    request_id: str | None = None,
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
    logger: logging.Logger,
    action: str,
    user_id: str,
    details: Dict[str, Any] | None = None,
):
    """사용자 액션 로그를 기록"""
    extra = {"user_id": user_id, "action": action}
    if details:
        extra.update(details)

    logger.info(f"사용자 액션: {action}", extra=extra)


def log_database_operation(
    logger: logging.Logger, operation: str, table: str, duration: float | None = None
):
    """데이터베이스 작업 로그를 기록"""
    extra: Dict[str, Any] = {"operation": operation, "table": table}
    if duration is not None:
        extra["duration"] = duration

    logger.info(f"DB 작업: {operation} on {table}", extra=extra)
