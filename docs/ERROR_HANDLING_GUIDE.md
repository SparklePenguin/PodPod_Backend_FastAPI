# 에러 처리 완벽 가이드 (Google Sheets 연계)

이 문서는 PodPod Backend의 도메인별 에러 처리 시스템 사용 가이드입니다.

## 목차

1. [전체 구조 개요](#전체-구조-개요)
2. [Google Sheets 에러 코드 시스템](#google-sheets-에러-코드-시스템)
3. [도메인별 Exception 정의](#도메인별-exception-정의)
4. [도메인별 Exception Handler 정의](#도메인별-exception-handler-정의)
5. [서비스에서 사용](#서비스에서-사용)
6. [새로운 도메인 추가](#새로운-도메인-추가)
7. [트러블슈팅](#트러블슈팅)

---

## 전체 구조 개요

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Sheets                           │
│  (에러 코드 중앙 관리: error_key, code, messages, etc.)      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓ (앱 시작 시 로드)
┌─────────────────────────────────────────────────────────────┐
│              app/core/error_codes.py                        │
│  (ERROR_CODES 딕셔너리, get_error_info 함수)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓ (참조)
┌─────────────────────────────────────────────────────────────┐
│              app/core/exceptions.py                         │
│  - BusinessException (기본)                                 │
│  - DomainException (Google Sheets 연계) ⭐                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓ (상속)
┌─────────────────────────────────────────────────────────────┐
│         app/features/{domain}/exceptions.py                 │
│  도메인별 Exception 클래스 정의                              │
│  - PodNotFoundException                                     │
│  - UserNotFoundException                                    │
│  - etc.                                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓ (처리)
┌─────────────────────────────────────────────────────────────┐
│      app/features/{domain}/exception_handlers.py            │
│  도메인별 Exception Handler 정의                             │
│  - EXCEPTION_HANDLERS 딕셔너리 export                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓ (자동 등록)
┌─────────────────────────────────────────────────────────────┐
│          app/core/exception_loader.py                       │
│  자동으로 모든 도메인의 핸들러를 발견하고 FastAPI에 등록      │
└─────────────────────────────────────────────────────────────┘
```

---

## Google Sheets 에러 코드 시스템

### 1. Google Sheets 구조

| error_key | code | message_ko | message_en | http_status | dev_note |
|-----------|------|------------|------------|-------------|----------|
| POD_NOT_FOUND | 4041 | 파티를 찾을 수 없습니다. | Pod not found | 404 | Pod does not exist |

### 2. 앱 시작 시 로드

```python
# app/core/startup.py (예시)
from app.core.error_codes import load_error_codes_from_sheets

async def startup_events():
    # Google Sheets에서 에러 코드 로드
    success = await load_error_codes_from_sheets(
        spreadsheet_id="YOUR_SPREADSHEET_ID",
        force_reload=False  # 캐시 사용
    )
    if success:
        print("✅ 에러 코드 로드 완료")
    else:
        print("⚠️ 에러 코드 로드 실패 (캐시 사용)")
```

### 3. 메시지 포맷팅

Google Sheets에 `{변수명}` 형태로 플레이스홀더를 사용하면 자동 치환:

```
# Google Sheets
message_ko: 파티를 찾을 수 없습니다. (ID: {pod_id})

# 코드
raise PodNotFoundException(pod_id=123)

# 결과
"파티를 찾을 수 없습니다. (ID: 123)"
```

---

## 도메인별 Exception 정의

### 1. DomainException 상속

`app/core/exceptions.py`의 `DomainException`을 상속받으면 Google Sheets에서 자동으로 에러 정보를 가져옵니다.

```python
# app/features/pods/exceptions.py
from app.core.exceptions import DomainException

class PodNotFoundException(DomainException):
    """파티를 찾을 수 없는 경우"""

    def __init__(self, pod_id: int):
        super().__init__(
            error_key="POD_NOT_FOUND",  # ← Google Sheets의 error_key
            format_params={"pod_id": pod_id},  # ← 메시지 포맷팅용
        )
        self.pod_id = pod_id  # ← 추가 속성 (선택)
```

### 2. 필수 파라미터

- **error_key**: Google Sheets에 등록된 에러 키
- **format_params**: 메시지 포맷팅용 파라미터 (dict)

### 3. 선택 파라미터

```python
class MyException(DomainException):
    def __init__(self):
        super().__init__(
            error_key="MY_ERROR",
            format_params={"foo": "bar"},
            override_message_ko="커스텀 메시지",  # Google Sheets 메시지 오버라이드
            override_message_en="Custom message",
            override_status_code=400,
            override_dev_note="Custom dev note",
        )
```

### 4. 여러 파라미터 포맷팅

```python
class PodFullException(DomainException):
    def __init__(self, pod_id: int, max_members: int, current_members: int):
        super().__init__(
            error_key="POD_FULL",
            format_params={
                "pod_id": pod_id,
                "max_members": max_members,
                "current_members": current_members,
            },
        )
        self.pod_id = pod_id
        self.max_members = max_members
        self.current_members = current_members
```

```
# Google Sheets
message_ko: 파티 정원이 가득 찼습니다. (현재 {current_members}/{max_members}명)

# 결과
"파티 정원이 가득 찼습니다. (현재 5/10명)"
```

---

## 도메인별 Exception Handler 정의

### 1. 핸들러 함수 작성

```python
# app/features/pods/exception_handlers.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.schemas import BaseResponse
from app.features.pods.exceptions import PodNotFoundException

logger = logging.getLogger(__name__)

async def pod_not_found_handler(request: Request, exc: PodNotFoundException):
    """PodNotFoundException 처리"""
    logger.warning(f"Pod not found: pod_id={exc.pod_id}, path={request.url.path}")

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,        # ← error_key
        error_code=exc.error_code_num,   # ← Google Sheets의 code (숫자)
        http_status=exc.status_code,     # ← Google Sheets의 http_status
        message_ko=exc.message_ko,       # ← Google Sheets의 message_ko (포맷팅됨)
        message_en=exc.message_en,       # ← Google Sheets의 message_en (포맷팅됨)
        dev_note=exc.dev_note,           # ← Google Sheets의 dev_note
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(by_alias=True)
    )
```

### 2. EXCEPTION_HANDLERS 딕셔너리 export (필수!)

```python
# app/features/pods/exception_handlers.py 하단에 추가

# ⭐ 이 딕셔너리가 있어야 자동 등록됨!
EXCEPTION_HANDLERS = {
    PodNotFoundException: pod_not_found_handler,
    PodFullException: pod_full_handler,
    # ... 다른 핸들러들
}
```

### 3. 자동 등록 확인

앱 시작 시 로그 확인:

```
✓ Loaded 10 handler(s) from app.features.pods.exception_handlers
✓ Registered handler for PodNotFoundException: pod_not_found_handler
✓ Registered handler for PodFullException: pod_full_handler
...
Domain exception handler registration complete: 10/10 handlers registered
```

---

## 서비스에서 사용

### 1. 기본 사용

```python
# app/features/pods/services/pod_service.py
from app.features.pods.exceptions import PodNotFoundException

class PodService:
    async def get_pod(self, pod_id: int):
        pod = await pod_repository.find_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)  # ← 이게 전부!
        return pod
```

### 2. 라우터는 간결하게

```python
# app/features/pods/routers/pod_router.py
@router.get("/{pod_id}")
async def get_pod(pod_id: int, service: PodService = Depends()):
    # try-catch 불필요! 예외는 자동으로 핸들러가 처리
    return await service.get_pod(pod_id)
```

### 3. 응답 예시

```http
GET /api/v1/pods/999

404 Not Found
{
  "data": null,
  "errorKey": "POD_NOT_FOUND",
  "errorCode": 4041,
  "httpStatus": 404,
  "messageKo": "파티를 찾을 수 없습니다. (ID: 999)",
  "messageEn": "Pod not found (ID: 999)",
  "devNote": "Pod with ID 999 does not exist in database"
}
```

---

## 새로운 도메인 추가

### 단계별 가이드

#### 1. Google Sheets에 에러 추가

```csv
error_key,code,message_ko,message_en,http_status,dev_note
USER_NOT_FOUND,2041,사용자를 찾을 수 없습니다.,User not found,404,User does not exist
```

#### 2. exceptions.py 생성

```bash
touch app/features/users/exceptions.py
```

```python
# app/features/users/exceptions.py
from app.core.exceptions import DomainException

class UserNotFoundException(DomainException):
    def __init__(self, user_id: int):
        super().__init__(
            error_key="USER_NOT_FOUND",
            format_params={"user_id": user_id},
        )
        self.user_id = user_id
```

#### 3. exception_handlers.py 생성

```bash
touch app/features/users/exception_handlers.py
```

```python
# app/features/users/exception_handlers.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.schemas import BaseResponse
from app.features.users.exceptions import UserNotFoundException

logger = logging.getLogger(__name__)

async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    logger.warning(f"User not found: {exc.user_id}")

    response = BaseResponse(
        data=None,
        error_key=exc.error_code,
        error_code=exc.error_code_num,
        http_status=exc.status_code,
        message_ko=exc.message_ko,
        message_en=exc.message_en,
        dev_note=exc.dev_note,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(by_alias=True)
    )

# ⭐ 필수!
EXCEPTION_HANDLERS = {
    UserNotFoundException: user_not_found_handler,
}
```

#### 4. 앱 재시작

```bash
# 자동 등록 확인
✓ Loaded 1 handler(s) from app.features.users.exception_handlers
✓ Registered handler for UserNotFoundException: user_not_found_handler
```

#### 5. 완료! 추가 작업 없음

`main.py`는 수정할 필요 없음. `exception_loader`가 자동으로 발견하고 등록합니다.

---

## 트러블슈팅

### Q1. 에러 메시지가 "에러가 발생했습니다. (ERROR_KEY)"로 나와요

**원인**: Google Sheets에 해당 `error_key`가 없음

**해결**:
1. `docs/ERROR_CODES_SHEET.md` 확인
2. Google Sheets에 에러 키 추가
3. 앱 재시작 또는 24시간 대기 (캐시 만료)

### Q2. 핸들러가 자동 등록되지 않아요

**원인**: `EXCEPTION_HANDLERS` 딕셔너리가 없거나 오타

**해결**:
```python
# exception_handlers.py 하단에 이게 있는지 확인
EXCEPTION_HANDLERS = {
    MyException: my_exception_handler,
}
```

### Q3. 포맷팅이 안 돼요 ("{pod_id}" 그대로 출력)

**원인**: `format_params` 키 이름이 Google Sheets의 플레이스홀더와 다름

**해결**:
```python
# Google Sheets: {pod_id}
# 코드:
format_params={"pod_id": 123}  # ✅ 일치
format_params={"id": 123}      # ❌ 불일치
```

### Q4. error_code_num이 9999로 나와요

**원인**: Google Sheets에서 로드 실패하고 기본값 사용 중

**해결**:
1. 캐시 파일 확인: `error_codes_backup.json`
2. 로그 확인: "Error key 'XXX' not found in ERROR_CODES"
3. Google Sheets에 해당 키 추가

### Q5. 다른 도메인에서 발생한 예외도 처리되나요?

**답변**: 네! 예외 타입으로 매칭되므로 어디서 발생하든 해당 도메인 핸들러가 처리합니다.

자세한 내용은 `docs/EXCEPTION_CROSS_DOMAIN.md` 참고

---

## 요약

### ✅ 장점

1. **중앙 관리**: Google Sheets에서 모든 에러 메시지 관리
2. **간결한 코드**: `error_key`만 지정하면 자동으로 메시지 로드
3. **자동 등록**: 도메인별 핸들러 자동 발견 및 등록
4. **포맷팅 지원**: 메시지에 변수 자동 치환
5. **확장성**: 새 도메인 추가 시 3개 파일만 생성

### 📝 핵심 파일

```
app/
├── core/
│   ├── error_codes.py           # Google Sheets 연계
│   ├── exceptions.py            # DomainException 정의
│   └── exception_loader.py      # 자동 등록 시스템
├── features/
│   └── {domain}/
│       ├── exceptions.py        # 도메인 Exception
│       └── exception_handlers.py # 도메인 Handler (EXCEPTION_HANDLERS export!)
└── docs/
    ├── ERROR_CODES_SHEET.md     # Google Sheets 추가 목록
    └── ERROR_HANDLING_GUIDE.md  # 이 문서
```

### 🚀 빠른 시작

1. Google Sheets에 에러 추가
2. `{domain}/exceptions.py` 작성 (DomainException 상속)
3. `{domain}/exception_handlers.py` 작성 (EXCEPTION_HANDLERS export)
4. 완료! (자동 등록)
