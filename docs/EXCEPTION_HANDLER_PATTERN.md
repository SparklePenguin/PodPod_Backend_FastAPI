# 도메인별 Exception Handler 패턴

## 문제점

기존 구조에서는 모든 에러 핸들러가 `app/core/exceptions.py`에 집중되어 있어:
- 도메인이 증가하면 파일이 비대해짐
- 도메인별 에러 처리 로직이 분리되지 않음
- 유지보수가 어려움

## 해결 방안

도메인별로 `exception_handlers.py`를 분리하고, 앱 시작 시 자동으로 등록하는 구조

### 디렉토리 구조

```
app/
├── core/
│   ├── exceptions.py              # 공통 Exception 클래스 정의
│   ├── exception_handlers.py      # 공통 핸들러 (HTTP, Validation 등)
│   └── exception_loader.py        # 자동 등록 시스템 (NEW)
├── features/
│   ├── pods/
│   │   ├── exceptions.py          # Pods 도메인 Exception 클래스
│   │   └── exception_handlers.py  # Pods 도메인 핸들러 (NEW)
│   ├── auth/
│   │   ├── exceptions.py          # Auth 도메인 Exception 클래스
│   │   └── exception_handlers.py  # Auth 도메인 핸들러 (NEW)
│   └── users/
│       ├── exceptions.py          # Users 도메인 Exception 클래스
│       └── exception_handlers.py  # Users 도메인 핸들러 (NEW)
└── main.py                         # 자동 등록 호출
```

## 구현 방법

### 1. 도메인별 Exception 클래스 정의

각 도메인에서 자신만의 Exception 클래스를 정의합니다.

**예시: `app/features/pods/exceptions.py`**

```python
from app.core.exceptions import BusinessException

class PodNotFoundException(BusinessException):
    """파티를 찾을 수 없는 경우"""
    def __init__(self, pod_id: int):
        super().__init__(
            error_code="POD_NOT_FOUND",
            message_ko=f"파티를 찾을 수 없습니다. (ID: {pod_id})",
            message_en=f"Pod not found (ID: {pod_id})",
            status_code=404,
            dev_note=f"Pod with ID {pod_id} does not exist"
        )
        self.pod_id = pod_id

class PodFullException(BusinessException):
    """파티가 가득 찬 경우"""
    def __init__(self, pod_id: int, max_members: int):
        super().__init__(
            error_code="POD_FULL",
            message_ko=f"파티 정원이 가득 찼습니다. (최대 {max_members}명)",
            message_en=f"Pod is full (max {max_members} members)",
            status_code=400,
            dev_note=f"Pod {pod_id} has reached maximum capacity"
        )
        self.pod_id = pod_id
        self.max_members = max_members
```

### 2. 도메인별 Exception Handler 정의

각 도메인에서 자신의 Exception을 처리하는 핸들러를 정의합니다.

**예시: `app/features/pods/exception_handlers.py`**

```python
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.schemas import BaseResponse
from app.features.pods.exceptions import PodNotFoundException, PodFullException

logger = logging.getLogger(__name__)

async def pod_not_found_handler(request: Request, exc: PodNotFoundException):
    """PodNotFoundException 처리"""
    logger.warning(f"Pod not found: {exc.pod_id}")

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=4041,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(by_alias=True)
    )

async def pod_full_handler(request: Request, exc: PodFullException):
    """PodFullException 처리"""
    logger.warning(f"Pod full: {exc.pod_id} (max: {exc.max_members})")

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=4001,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(by_alias=True)
    )

# 핸들러 매핑 (자동 등록에 사용)
EXCEPTION_HANDLERS = {
    PodNotFoundException: pod_not_found_handler,
    PodFullException: pod_full_handler,
}
```

### 3. 자동 등록 시스템 구현

**`app/core/exception_loader.py`**

```python
import importlib
import logging
from pathlib import Path
from typing import Callable, Dict, Type

from fastapi import FastAPI

logger = logging.getLogger(__name__)

def discover_exception_handlers(base_path: str = "app/features") -> Dict[Type[Exception], Callable]:
    """
    features 디렉토리에서 모든 exception_handlers.py를 찾아 핸들러를 수집합니다.

    Returns:
        {ExceptionClass: handler_function} 형태의 딕셔너리
    """
    handlers = {}
    features_path = Path(base_path)

    if not features_path.exists():
        logger.warning(f"Features path not found: {base_path}")
        return handlers

    # 모든 exception_handlers.py 파일 찾기
    for handler_file in features_path.rglob("exception_handlers.py"):
        # 상대 경로를 모듈 경로로 변환 (예: app/features/pods/exception_handlers.py -> app.features.pods.exception_handlers)
        module_path = str(handler_file.with_suffix("")).replace("/", ".")

        try:
            # 동적으로 모듈 import
            module = importlib.import_module(module_path)

            # EXCEPTION_HANDLERS 딕셔너리가 있는지 확인
            if hasattr(module, "EXCEPTION_HANDLERS"):
                module_handlers = getattr(module, "EXCEPTION_HANDLERS")
                handlers.update(module_handlers)
                logger.info(f"Loaded {len(module_handlers)} handlers from {module_path}")
            else:
                logger.warning(f"No EXCEPTION_HANDLERS found in {module_path}")

        except Exception as e:
            logger.error(f"Failed to load handlers from {module_path}: {str(e)}")

    return handlers

def register_exception_handlers(app: FastAPI, base_path: str = "app/features"):
    """
    앱에 도메인별 exception handler를 자동으로 등록합니다.

    Args:
        app: FastAPI 애플리케이션 인스턴스
        base_path: features 디렉토리 경로
    """
    handlers = discover_exception_handlers(base_path)

    for exception_class, handler_func in handlers.items():
        app.add_exception_handler(exception_class, handler_func)
        logger.info(f"Registered handler for {exception_class.__name__}")

    logger.info(f"Total {len(handlers)} domain-specific exception handlers registered")
```

### 4. main.py에서 자동 등록 호출

**`main.py`**

```python
from app.core.exception_loader import register_exception_handlers

# ... (기존 코드)

# 공통 예외 핸들러 등록 (기존)
app.add_exception_handler(HTTPException, cast(Any, http_exception_handler))
app.add_exception_handler(StarletteHTTPException, cast(Any, http_exception_handler))
app.add_exception_handler(RequestValidationError, cast(Any, validation_exception_handler))
app.add_exception_handler(ValueError, cast(Any, value_error_handler))
app.add_exception_handler(BusinessException, cast(Any, business_exception_handler))
app.add_exception_handler(Exception, cast(Any, general_exception_handler))

# 도메인별 예외 핸들러 자동 등록 (NEW)
register_exception_handlers(app)
```

## 사용 예시

### 서비스 레이어에서 예외 발생

```python
# app/features/pods/services/pod_service.py

from app.features.pods.exceptions import PodNotFoundException, PodFullException

class PodService:
    async def get_pod(self, pod_id: int):
        pod = await pod_repository.find_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)
        return pod

    async def join_pod(self, pod_id: int, user_id: int):
        pod = await self.get_pod(pod_id)

        if len(pod.members) >= pod.max_members:
            raise PodFullException(pod_id, pod.max_members)

        # 참여 로직...
```

### 라우터에서는 예외 처리 불필요

```python
# app/features/pods/router.py

@router.get("/{pod_id}")
async def get_pod(pod_id: int, service: PodService = Depends()):
    # 예외 처리 코드 없음!
    # PodNotFoundException이 발생하면 자동으로 pod_not_found_handler가 처리
    return await service.get_pod(pod_id)

@router.post("/{pod_id}/join")
async def join_pod(pod_id: int, user: User = Depends(), service: PodService = Depends()):
    # 예외 처리 코드 없음!
    # PodFullException이 발생하면 자동으로 pod_full_handler가 처리
    return await service.join_pod(pod_id, user.id)
```

## 장점

1. **관심사 분리**: 각 도메인이 자신의 에러를 관리
2. **확장성**: 새 도메인 추가 시 `exception_handlers.py`만 추가하면 자동 등록
3. **유지보수성**: 도메인별로 파일이 분리되어 관리 용이
4. **라우터 간결성**: 라우터에서 예외 처리 코드 불필요
5. **테스트 용이성**: 도메인별로 핸들러 테스트 가능

## 주의사항

1. **핸들러 우선순위**: FastAPI는 가장 구체적인 예외부터 매칭하므로, 도메인별 예외가 BusinessException보다 먼저 처리됨
2. **EXCEPTION_HANDLERS 규칙**: 각 `exception_handlers.py`는 반드시 `EXCEPTION_HANDLERS` 딕셔너리를 export해야 함
3. **순환 참조 주의**: exception_loader는 런타임에 동적으로 import하므로 순환 참조 문제 없음

## 마이그레이션 가이드

기존 코드를 점진적으로 마이그레이션할 수 있습니다:

1. `app/core/exception_loader.py` 생성
2. 한 도메인씩 `exceptions.py`와 `exception_handlers.py` 추가
3. `main.py`에서 자동 등록 호출 추가
4. 기존 `core/exceptions.py`의 도메인별 코드를 점진적으로 제거
