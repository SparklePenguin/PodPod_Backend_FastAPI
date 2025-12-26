# 도메인 간 예외 처리 (Cross-Domain Exception Handling)

## 질문: A 도메인에서 B 도메인 서비스를 호출하면 예외는 어디서 처리되나?

**답변: B 도메인의 exception handler가 처리합니다.**

## 동작 원리

FastAPI의 exception handler는 **전역적으로** 등록되며, 예외가 발생한 **위치가 아닌 예외의 타입**으로 매칭됩니다.

### 예시 시나리오

```python
# ============================================
# B 도메인: Users
# ============================================

# app/features/users/exceptions.py
class UserNotFoundException(BusinessException):
    def __init__(self, user_id: int):
        super().__init__(
            error_code="USER_NOT_FOUND",
            message_ko=f"사용자를 찾을 수 없습니다. (ID: {user_id})",
            message_en=f"User not found (ID: {user_id})",
            status_code=404,
        )

# app/features/users/exception_handlers.py
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    logger.warning(f"[USERS] User not found: {exc.user_id}")
    # ... BaseResponse 반환

EXCEPTION_HANDLERS = {
    UserNotFoundException: user_not_found_handler,
}

# app/features/users/services/user_service.py
class UserService:
    async def get_user(self, user_id: int):
        user = await user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)  # ← 여기서 발생
        return user


# ============================================
# A 도메인: Pods (B 도메인 의존)
# ============================================

# app/features/pods/services/pod_service.py
class PodService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def create_pod(self, user_id: int, pod_data: dict):
        # B 도메인(users) 서비스 호출
        user = await self.user_service.get_user(user_id)  # ← UserNotFoundException 전파

        # 파티 생성 로직...
        pod = Pod(**pod_data, host_id=user.id)
        return await pod_repository.save(pod)

# app/features/pods/routers/pod_router.py
@router.post("/")
async def create_pod(
    user_id: int,
    pod_data: PodCreateRequest,
    service: PodService = Depends()
):
    # ← UserNotFoundException이 여기까지 전파되면?
    return await service.create_pod(user_id, pod_data.dict())
```

### 호출 흐름 및 예외 전파

```
1. 클라이언트 → POST /api/v1/pods (파티 생성 요청)
                    ↓
2. pod_router.create_pod() 호출
                    ↓
3. pod_service.create_pod() 호출
                    ↓
4. user_service.get_user() 호출
                    ↓
5. UserNotFoundException 발생 ←
                    ↓
6. pod_service.create_pod()로 전파
                    ↓
7. pod_router.create_pod()로 전파
                    ↓
8. FastAPI exception handler 매칭
   - 예외 타입: UserNotFoundException
   - 등록된 핸들러: user_not_found_handler ✓
                    ↓
9. user_not_found_handler 실행 (B 도메인 핸들러!)
                    ↓
10. 클라이언트 ← 404 응답
    {
      "data": null,
      "errorCode": 4041,
      "errorKey": "USER_NOT_FOUND",
      "httpStatus": 404,
      "messageKo": "사용자를 찾을 수 없습니다. (ID: 123)",
      "messageEn": "User not found (ID: 123)",
      "devNote": "User with ID 123 does not exist"
    }
```

## 장점

### 1. 일관된 에러 응답
각 도메인의 예외는 항상 해당 도메인 핸들러가 처리하므로 일관성 유지

```python
# users 도메인 예외는 어디서 발생하든 users handler가 처리
# pods 도메인 예외는 어디서 발생하든 pods handler가 처리
# → 에러 응답 형식 일관성 보장
```

### 2. 관심사 분리
각 도메인이 자신의 예외만 책임지면 됨

### 3. 재사용성
B 도메인 서비스를 여러 도메인에서 사용해도 예외 처리 로직 중복 불필요

## 주의사항 및 잠재적 문제

### 문제 1: 컨텍스트 불일치

파티 생성 API에서 "사용자를 찾을 수 없습니다"라는 메시지가 나올 수 있음

```http
POST /api/v1/pods
{
  "user_id": 999,
  "title": "새 파티"
}

→ 404 Response
{
  "messageKo": "사용자를 찾을 수 없습니다. (ID: 999)"
}
```

사용자 입장에서는 "파티를 만들려고 했는데 왜 사용자 에러가 나오지?"라고 혼란스러울 수 있음

### 해결 방법

#### 방법 1: 그대로 사용 (권장)

대부분의 경우 에러 메시지가 명확하면 문제없음. 클라이언트는 `errorKey`를 보고 처리 가능

```javascript
// 클라이언트에서 errorKey로 분기
if (error.errorKey === "USER_NOT_FOUND") {
  showAlert("유효하지 않은 사용자입니다.");
} else if (error.errorKey === "POD_NOT_FOUND") {
  showAlert("파티를 찾을 수 없습니다.");
}
```

#### 방법 2: 도메인 경계에서 예외 래핑

A 도메인에서 B 도메인 예외를 잡아서 A 도메인 예외로 변환

```python
# app/features/pods/services/pod_service.py
from app.features.users.exceptions import UserNotFoundException
from app.features.pods.exceptions import InvalidPodHostException

class PodService:
    async def create_pod(self, user_id: int, pod_data: dict):
        try:
            # B 도메인 호출
            user = await self.user_service.get_user(user_id)
        except UserNotFoundException:
            # A 도메인 예외로 래핑
            raise InvalidPodHostException(user_id)

        # 파티 생성 로직...
        pod = Pod(**pod_data, host_id=user.id)
        return await pod_repository.save(pod)
```

```python
# app/features/pods/exceptions.py
class InvalidPodHostException(BusinessException):
    """유효하지 않은 파티 호스트"""
    def __init__(self, user_id: int):
        super().__init__(
            error_code="INVALID_POD_HOST",
            message_ko="파티를 생성할 수 없습니다. 유효하지 않은 호스트입니다.",
            message_en="Cannot create pod. Invalid host.",
            status_code=400,
            dev_note=f"User {user_id} does not exist",
        )
```

**장점:**
- 도메인 컨텍스트에 맞는 에러 메시지
- 명확한 의미 전달

**단점:**
- 코드 중복 (try-except 반복)
- 유지보수 부담

#### 방법 3: 조건부 래핑 (선택적 적용)

**중요한 API**에만 래핑 적용, 나머지는 그대로 사용

```python
class PodService:
    # 공개 API (외부 노출) → 래핑
    async def create_pod(self, user_id: int, pod_data: dict):
        try:
            user = await self.user_service.get_user(user_id)
        except UserNotFoundException:
            raise InvalidPodHostException(user_id)
        # ...

    # 내부 API → 그대로 전파
    async def _add_member_internal(self, pod_id: int, user_id: int):
        user = await self.user_service.get_user(user_id)  # 예외 그대로 전파
        # ...
```

## 권장 사항

### 1. 대부분의 경우: 그대로 사용

```python
# ✅ 간단하고 명확
async def create_pod(self, user_id: int, pod_data: dict):
    user = await self.user_service.get_user(user_id)
    # UserNotFoundException이 발생하면 users handler가 처리
    # 에러 메시지가 명확하므로 문제없음
```

### 2. 사용자 경험이 중요한 경우: 선택적 래핑

```python
# ✅ 공개 API에서만 래핑
async def create_pod_public(self, user_id: int, pod_data: dict):
    try:
        user = await self.user_service.get_user(user_id)
    except UserNotFoundException:
        # 도메인 컨텍스트에 맞게 변환
        raise InvalidPodHostException(user_id)
```

### 3. 내부 API: 항상 그대로 전파

```python
# ✅ 내부 함수는 예외를 그대로 전파
async def _internal_helper(self, user_id: int):
    user = await self.user_service.get_user(user_id)
    # 예외 처리 안 함
```

## 예외 우선순위

FastAPI는 **가장 구체적인 예외**부터 매칭합니다.

```python
# 등록 순서:
1. PodNotFoundException (구체적)
2. UserNotFoundException (구체적)
3. BusinessException (일반적)
4. Exception (최상위)

# 매칭 순서:
PodNotFoundException 발생 → pod_not_found_handler
UserNotFoundException 발생 → user_not_found_handler
기타 BusinessException 발생 → business_exception_handler
기타 모든 예외 → general_exception_handler
```

## 테스트 예시

```python
import pytest
from fastapi.testclient import TestClient

def test_create_pod_with_invalid_user(client: TestClient):
    """존재하지 않는 사용자로 파티 생성 시도"""
    response = client.post(
        "/api/v1/pods",
        json={"user_id": 999, "title": "새 파티"}
    )

    # B 도메인(users) 핸들러가 처리한 응답
    assert response.status_code == 404
    assert response.json()["errorKey"] == "USER_NOT_FOUND"
    assert "사용자를 찾을 수 없습니다" in response.json()["messageKo"]
```

## 정리

| 시나리오 | 예외 발생 위치 | 처리 핸들러 | 이유 |
|---------|--------------|-----------|------|
| Pods API → Pods 서비스 | Pods 서비스 | Pods handler | 같은 도메인 |
| Pods API → Pods 서비스 → Users 서비스 | Users 서비스 | **Users handler** | 예외 타입으로 매칭 |
| Users API → Users 서비스 | Users 서비스 | Users handler | 같은 도메인 |

**핵심: 예외가 발생한 위치가 아니라 예외의 타입으로 핸들러가 결정됩니다.**
