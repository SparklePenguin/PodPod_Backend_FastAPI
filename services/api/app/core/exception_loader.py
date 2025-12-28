"""
도메인별 Exception Handler 자동 등록 시스템

이 모듈은 app/features 하위의 모든 도메인에서 exception_handlers.py를 찾아
자동으로 FastAPI 앱에 등록합니다.

Usage:
    from app.core.exception_loader import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)
"""

import importlib
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Type

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def discover_exception_handlers(
    base_path: str | None = None,
) -> Dict[Type[Exception], Callable]:
    """
    features 디렉토리에서 모든 exception_handlers.py를 찾아 핸들러를 수집합니다.

    각 exception_handlers.py 파일은 다음과 같은 형태를 가져야 합니다:

    ```python
    # app/features/domain/exception_handlers.py

    async def my_exception_handler(request: Request, exc: MyException):
        # 처리 로직
        return JSONResponse(...)

    # 이 딕셔너리가 있어야 자동 등록됨
    EXCEPTION_HANDLERS = {
        MyException: my_exception_handler,
    }
    ```

    Args:
        base_path: features 디렉토리 경로 (기본값: "app/features")

    Returns:
        {ExceptionClass: handler_function} 형태의 딕셔너리
    """
    handlers: Dict[Type[Exception], Callable] = {}

    # base_path가 None이면 현재 파일 기준으로 절대 경로 계산
    if base_path is None:
        # exception_loader.py -> app/core/ -> app/ -> features/
        current_file = Path(__file__).resolve()
        app_dir = current_file.parent.parent  # app/ 디렉토리
        features_path = app_dir / "features"
    else:
        features_path = Path(base_path)

    if not features_path.exists():
        logger.warning(f"Features path not found: {features_path}")
        return handlers

    # 모든 exception_handlers.py 파일 찾기
    handler_files = list(features_path.rglob("exception_handlers.py"))

    if not handler_files:
        logger.info(f"No exception_handlers.py files found in {base_path}")
        return handlers

    logger.info(f"Found {len(handler_files)} exception_handlers.py files")

    for handler_file in handler_files:
        # 상대 경로를 모듈 경로로 변환
        # 예: app/features/pods/exception_handlers.py -> app.features.pods.exception_handlers
        module_path = str(handler_file.with_suffix("")).replace("/", ".")

        try:
            # 동적으로 모듈 import
            module = importlib.import_module(module_path)

            # EXCEPTION_HANDLERS 딕셔너리가 있는지 확인
            if hasattr(module, "EXCEPTION_HANDLERS"):
                module_handlers = getattr(module, "EXCEPTION_HANDLERS")

                if not isinstance(module_handlers, dict):
                    logger.warning(
                        f"EXCEPTION_HANDLERS in {module_path} is not a dict, skipping"
                    )
                    continue

                # 핸들러 등록
                for exc_class, handler_func in module_handlers.items():
                    if not isinstance(exc_class, type) or not issubclass(
                        exc_class, Exception
                    ):
                        logger.warning(
                            f"Invalid exception class {exc_class} in {module_path}, skipping"
                        )
                        continue

                    if not callable(handler_func):
                        logger.warning(
                            f"Invalid handler function for {exc_class.__name__} in {module_path}, skipping"
                        )
                        continue

                    handlers[exc_class] = handler_func

                logger.info(
                    f"✓ Loaded {len(module_handlers)} handler(s) from {module_path}"
                )
            else:
                logger.debug(f"No EXCEPTION_HANDLERS found in {module_path}")

        except ImportError as e:
            logger.error(f"Failed to import {module_path}: {str(e)}")
        except Exception as e:
            logger.error(
                f"Failed to load handlers from {module_path}: {type(e).__name__}: {str(e)}"
            )

    return handlers


def register_exception_handlers(
    app: FastAPI, base_path: str | None = None, verbose: bool = True
):
    """
    앱에 도메인별 exception handler를 자동으로 등록합니다.

    이 함수는 main.py에서 호출되며, features 디렉토리의 모든 도메인에서
    exception_handlers.py를 찾아 자동으로 등록합니다.

    Args:
        app: FastAPI 애플리케이션 인스턴스
        base_path: features 디렉토리 경로 (기본값: None, 자동으로 app/features 찾기)
        verbose: 상세 로그 출력 여부

    Example:
        ```python
        # main.py
        from app.core.exception_loader import register_exception_handlers

        app = FastAPI()

        # 공통 핸들러 등록
        app.add_exception_handler(HTTPException, http_exception_handler)
        # ...

        # 도메인별 핸들러 자동 등록
        register_exception_handlers(app)
        ```
    """
    if verbose:
        logger.info("=" * 60)
        logger.info("Starting domain exception handler registration...")
        logger.info("=" * 60)

    handlers = discover_exception_handlers(base_path)

    if not handlers:
        logger.warning("No domain exception handlers found")
        return

    # 핸들러 등록
    registered_count = 0
    for exception_class, handler_func in handlers.items():
        try:
            # FastAPI에 핸들러 등록
            # 타입 체크를 위한 Any 캐스팅
            from typing import cast

            app.add_exception_handler(exception_class, cast(Any, handler_func))
            registered_count += 1

            if verbose:
                logger.info(
                    f"✓ Registered handler for {exception_class.__name__}: {handler_func.__name__}"
                )

        except Exception as e:
            logger.error(
                f"Failed to register handler for {exception_class.__name__}: {str(e)}"
            )

    if verbose:
        logger.info("=" * 60)
        logger.info(
            f"Domain exception handler registration complete: {registered_count}/{len(handlers)} handlers registered"
        )
        logger.info("=" * 60)
