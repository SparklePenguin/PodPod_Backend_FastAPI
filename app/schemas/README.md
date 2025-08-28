# Schemas 네이밍 규칙

## 📋 개요
이 문서는 FastAPI 프로젝트의 Pydantic 스키마 네이밍 규칙을 정의합니다.

## 🏗️ 구조

### 1. Request 스키마
- **규칙**: `{Action}Request`
- **설명**: 특정 요청을 처리하는 스키마
- **예시**:
  ```python
  class SignUpRequest(BaseModel):
      email: str
      password: str
      username: Optional[str] = None
  ```

### 2. Data 스키마 (Common)
- **규칙**: `{Action}Data`
- **설명**: `common.py`에서 반환하는 데이터 구조
- **예시**:
  ```python
  class SignInData(BaseModel):
      credential: Credential
      user: User
  ```

### 3. 내부 구성 요소
- **규칙**: `{Name}` (Data 접미사 없음)
- **설명**: Data 스키마 내부에 들어가는 구성 요소
- **예시**:
  ```python
  class Credential(BaseModel):
      access_token: str
      refresh_token: str

  class User(BaseModel):
      id: int
      email: str
      username: Optional[str] = None
  ```

## 📝 Response 규칙

### 1. 성공 응답
- **규칙**: 항상 `SuccessResponse` 사용
- **구조**:
  ```python
  class SuccessResponse(BaseModel):
      code: int
      message: str  # 스네이크 케이스
      data: Optional[Any] = None
  ```

### 2. 에러 응답
- **규칙**: 항상 `ErrorResponse` 사용
- **구조**:
  ```python
  class ErrorResponse(BaseModel):
      error_code: str
      status: int
      message: str  # 스네이크 케이스
  ```

## 📝 Message 네이밍 규칙

### 1. 스네이크 케이스 사용
- **올바른 예시**:
  - `"user_created_successfully"`
  - `"kakao_login_success"`
  - `"invalid_credentials"`
  - `"email_already_exists"`

- **잘못된 예시**:
  - `"userCreatedSuccessfully"`
  - `"kakaoLoginSuccess"`
  - `"InvalidCredentials"`

### 2. 메시지 패턴
- **성공**: `{action}_{result}`
- **에러**: `{error_type}_{description}`

## 📝 예시

### 완전한 예시
```python
# Request
class SignUpRequest(BaseModel):
    email: str
    password: str
    username: Optional[str] = None

# Data (Common)
class SignInData(BaseModel):
    credential: Credential
    user: User

# 내부 구성 요소
class Credential(BaseModel):
    access_token: str
    refresh_token: str

class User(BaseModel):
    id: int
    email: str
    username: Optional[str] = None

# API 응답 예시
@router.post("/signup")
async def signup(request: SignUpRequest):
    # 성공 시
    return SuccessResponse(
        code=201,
        message="user_created_successfully",
        data=SignInData(
            credential=Credential(...),
            user=User(...)
        )
    )

    # 에러 시
    raise HTTPException(
        status_code=400,
        detail=ErrorResponse(
            error_code="email_already_exists",
            status=400,
            message="email_already_exists"
        )
    )
```

## 📝 마이그레이션 가이드

### 기존 코드 수정
1. **Request 클래스**: `UserCreate` → `SignUpRequest`
2. **Data 클래스**: `UserResponse` → `SignInData`
3. **내부 클래스**: `UserDto` → `User`
4. **메시지**: `"User created"` → `"user_created_successfully"`

## ✅ 체크리스트

- [ ] Request 클래스에 `Request` 접미사 사용
- [ ] Data 클래스에 `{Action}Data` 패턴 사용
- [ ] 내부 구성 요소에 `Data` 접미사 제거
- [ ] 모든 응답이 `SuccessResponse` 또는 `ErrorResponse` 사용
- [ ] 모든 메시지가 스네이크 케이스로 작성
- [ ] 일관된 네이밍 패턴 적용
