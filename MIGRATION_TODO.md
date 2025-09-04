# 🚀 PodPod Backend 업데이트 마이그레이션 가이드

이 파일은 다른 환경에서 최근 업데이트된 기능들을 적용하기 위한 단계별 가이드입니다.

## 📋 주요 변경사항 요약

1. **사용자 상태 관리 시스템 개선** (`needsOnboarding` → `UserState` enum)
2. **토큰 블랙리스트 시스템 구현**
3. **API 응답 형식 카멜케이스 통일**
4. **사용자 응답에 성향 정보 추가**
5. **🆕 OAuth 에러 처리 개선** (카카오/구글 로그인 안정성 향상)
6. **🆕 사용자 상태 로직 실시간 계산** (DB 기반 동적 상태 결정)
7. **🆕 프로필 설정 여부 자동 감지** (생성/업데이트 시간 비교)

---

## 🔧 단계별 적용 가이드

### 1. UserState Enum 생성
```bash
# 새 파일 생성: app/models/user_state.py
```

```python
from enum import Enum
축

class UserState(str, Enum):
    """사용자 온보딩 상태"""
    PREFERRED_ARTISTS = "PREFERRED_ARTISTS"  # 선호 아티스트 설정 필요
    TENDENCY_TEST = "TENDENCY_TEST"          # 성향 테스트 필요
    PROFILE_SETTING = "PROFILE_SETTING"      # 프로필 설정 필요
    COMPLETED = "COMPLETED"                  # 온보딩 완료
```

### 2. User 모델 업데이트
**파일:** `app/models/user.py`

```python
# 기존 imports에 추가
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from app.models.user_state import UserState

# User 클래스에서 변경
class User(Base):
    # ... 기존 필드들 ...

    # 변경: needs_onboarding을 state로 교체
    # needs_onboarding = Column(Boolean, default=True)  # 이 줄 삭제
    state = Column(Enum(UserState), default=UserState.PREFERRED_ARTISTS)  # 이 줄 추가
```

### 3. UserDto 스키마 업데이트
**파일:** `app/schemas/user.py`

```python
# imports에 추가
from app.models.user_state import UserState

# UserDto 클래스 수정
class UserDto(BaseModel):
    id: int = Field(alias="id")
    email: Optional[str] = Field(default=None, alias="email")
    username: Optional[str] = Field(default=None, alias="username")
    nickname: Optional[str] = Field(default=None, alias="nickname")
    profile_image: Optional[str] = Field(default=None, alias="profileImage")
    intro: Optional[str] = Field(default=None, alias="intro")

    # 변경: needs_onboarding을 state와 tendency_type으로 교체
    # needs_onboarding: bool = Field(alias="needsOnboarding")  # 이 줄 삭제
    state: UserState = Field(alias="state")  # 새로 추가
    tendency_type: Optional[str] = Field(default=None, alias="tendencyType")  # 새로 추가

    created_at: Optional[datetime.datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime.datetime] = Field(default=None, alias="updatedAt")
```

### 4. 토큰 블랙리스트 시스템 추가
**파일:** `app/core/security.py`

```python
# 파일 상단에 추가 (settings import 아래)
# 토큰 블랙리스트 (메모리 기반, 추후 Redis 등으로 대체 가능)
_token_blacklist = set()


def add_token_to_blacklist(token: str):
    """토큰을 블랙리스트에 추가"""
    _token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """토큰이 블랙리스트에 있는지 확인"""
    return token in _token_blacklist


def clear_blacklist():
    """블랙리스트 초기화 (테스트용)"""
    _token_blacklist.clear()


# 새로운 예외 클래스 추가 (TokenDecodeError 클래스 아래)
class TokenBlacklistedError(Exception):
    """토큰이 블랙리스트에 있을 때"""

    status: int = 401
    code: str = "token_blacklisted"
    message: str = "무효화된 토큰입니다."


# verify_token 함수 수정
def verify_token(token: str, token_type: str = None) -> int:
    """토큰 검증 후 user_id 리턴, 실패시 도메인 에러 발생"""
    # 블랙리스트 확인 추가
    if is_token_blacklisted(token):
        raise TokenBlacklistedError()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise TokenInvalidError()

        # 토큰 타입 검증 (지정된 경우)
        if token_type:
            actual_type = payload.get("type")
            if actual_type != token_type:
                raise TokenInvalidError()

        return int(user_id)

    except ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise TokenInvalidError()
    except Exception:
        raise TokenDecodeError()


# verify_refresh_token 함수 추가
def verify_refresh_token(token: str) -> int:
    """리프레시 토큰 전용 검증"""
    return verify_token(token, "refresh")
```

### 5. CredentialDto 카멜케이스 변경
**파일:** `app/schemas/auth.py`

```python
# CredentialDto 클래스 수정
class CredentialDto(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")

    model_config = {"populate_by_name": True}
```

### 6. SessionService 업데이트
**파일:** `app/services/session_service.py`

```python
# imports에 추가
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    add_token_to_blacklist,  # 새로 추가
    verify_password,  # 새로 추가
)
from app.schemas.common import SuccessResponse, ErrorResponse  # 새로 추가

# SessionService 클래스에 메서드들 추가
class SessionService:
    # ... 기존 메서드들 ...

    async def login(self, login_data):
        """이메일 로그인"""
        from app.schemas.auth import SignInResponse
        from app.schemas.user import UserDto

        # 이메일로 사용자 찾기
        user = await self.user_crud.get_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error_code="invalid_credentials",
                    status=401,
                    message="이메일 또는 비밀번호가 잘못되었습니다."
                ).model_dump()
            )

        # 비밀번호 확인 (일반 로그인의 경우)
        if login_data.password and user.hashed_password:
            if not verify_password(login_data.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=ErrorResponse(
                        error_code="invalid_credentials",
                        status=401,
                        message="이메일 또는 비밀번호가 잘못되었습니다."
                    ).model_dump()
                )

        # 토큰 생성
        credential = await self.create_token(user.id)

        # SignInResponse 생성
        sign_in_response = SignInResponse(
            credential=credential,
            user=UserDto.model_validate(user, from_attributes=True)
        )

        return SuccessResponse(
            code=200,
            message="login_successful",
            data=sign_in_response.model_dump(by_alias=True)
        )

    async def logout(self, access_token: str):
        """로그아웃 (토큰 무효화)"""
        # 액세스 토큰을 블랙리스트에 추가하여 무효화
        add_token_to_blacklist(access_token)

        return SuccessResponse(
            code=200,
            message="logout_successful",
            data={"message": "토큰이 무효화되었습니다."},
        )
```

### 7. 세션 엔드포인트 업데이트
**파일:** `app/api/v1/endpoints/sessions.py`

```python
# 모든 경로를 "/" 대신 ""로 변경
@router.post("")  # "/" 대신 ""
@router.put("")   # "/" 대신 ""
@router.delete("") # "/" 대신 ""

# 토큰 갱신 응답 수정
def refresh_session():
    # ... 기존 코드 ...
    try:
        credential = await auth_service.refresh_token(refresh_data.refresh_token)
        return SuccessResponse(
            code=200,
            message="token_refreshed_successfully",
            data=credential.model_dump(by_alias=True),  # credential을 바로 data에
        )
    except (TokenExpiredError, TokenInvalidError, TokenDecodeError, TokenBlacklistedError) as e:
        # TokenBlacklistedError 추가
```

### 8. OAuth 서비스 응답 형식 수정
**파일:** `app/services/oauth_service.py`

```python
# 로그인 성공 응답 수정
async def authenticate_user():
    # ... 기존 코드 ...

    sign_in_response = SignInResponse(
        credential=CredentialDto(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
        ),
        user=UserDto.model_validate(user, from_attributes=True),
    )

    return SuccessResponse(
        code=200,
        message=f"{oauth_provider}_login_success",
        data=sign_in_response.model_dump(by_alias=True),  # by_alias=True 추가
    )
```

### 9. 사용자 업데이트 응답 형식 수정
**파일:** `app/api/v1/endpoints/users.py`

```python
# 사용자 업데이트 엔드포인트 수정
async def update_user_profile():
    # ... 기존 코드 ...

    user = await user_service.update_profile(current_user_id, profile_data)
    return SuccessResponse(
        code=200,
        message="user_updated_successfully",
        data=user.model_dump(by_alias=True)  # {"user": user} 대신 직접
    )
```

### 10. UserService 상태 로직 추가
**파일:** `app/services/user_service.py`

```python
# imports에 추가
from app.models.user_state import UserState

# UserService 클래스에 메서드들 추가
class UserService:
    # ... 기존 메서드들 ...

    def _determine_user_state(self, user, has_preferred_artists: bool, has_tendency_result: bool) -> UserState:
        """사용자 온보딩 상태 결정"""
        # 1. 선호 아티스트가 없으면 PREFERRED_ARTISTS
        if not has_preferred_artists:
            return UserState.PREFERRED_ARTISTS

        # 2. 성향 테스트 결과가 없으면 TENDENCY_TEST
        if not has_tendency_result:
            return UserState.TENDENCY_TEST

        # 3. 닉네임이 없으면 PROFILE_SETTING
        if not user.nickname:
            return UserState.PROFILE_SETTING

        # 4. 모든 조건을 만족하면 COMPLETED
        return UserState.COMPLETED

    async def _get_user_tendency_type(self, user_id: int) -> Optional[str]:
        """사용자의 성향 타입 조회"""
        # UserTendencyResult에서 사용자의 최신 성향 결과 조회
        # 실제 구현에서는 CRUD를 통해 조회해야 함
        # 임시로 None 반환
        return None

    def _prepare_user_dto_data(self, user) -> dict:
        """UserDto 생성을 위한 데이터 준비"""
        # 기본 사용자 정보
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "nickname": user.nickname,
            "profile_image": user.profile_image,
            "intro": user.intro,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        # 상태 결정을 위한 정보 수집 (임시로 False 값 사용)
        has_preferred_artists = False  # 실제로는 DB에서 조회
        has_tendency_result = False    # 실제로는 DB에서 조회

        # 사용자 상태 결정
        user_data["state"] = self._determine_user_state(user, has_preferred_artists, has_tendency_result)

        # 성향 타입 추가 (임시로 None)
        user_data["tendency_type"] = None

        return user_data
```

---

## 🗄️ 데이터베이스 마이그레이션

### 마이그레이션 생성 (설정 문제 해결 후)
```bash
# 가상환경 활성화
source venv/bin/activate

# 마이그레이션 생성
alembic revision --autogenerate -m "Add user state enum and remove needs_onboarding"

# 마이그레이션 실행
alembic upgrade head
```

### 기존 데이터 마이그레이션 스크립트
기존 `needs_onboarding` 값에 따라 적절한 `state` 값으로 변환:

```sql
-- needs_onboarding이 true인 사용자들을 PREFERRED_ARTISTS로 설정
UPDATE users SET state = 'PREFERRED_ARTISTS' WHERE needs_onboarding = true;

-- needs_onboarding이 false인 사용자들을 COMPLETED로 설정
UPDATE users SET state = 'COMPLETED' WHERE needs_onboarding = false;
```

---

## 📝 변경된 API 응답 형식

### 로그인/회원가입 응답
```json
{
  "code": 200,
  "message": "login_successful",
  "data": {
    "credential": {
      "accessToken": "...",
      "refreshToken": "..."
    },
    "user": {
      "id": 1,
      "email": "user@example.com",
      "nickname": "nickname",
      "profileImage": null,
      "state": "PREFERRED_ARTISTS",
      "tendencyType": "quietMate",
      "..."
    }
  }
}
```

### 리프레시 토큰 응답
```json
{
  "code": 200,
  "message": "token_refreshed_successfully",
  "data": {
    "accessToken": "...",
    "refreshToken": "..."
  }
}
```

### 사용자 업데이트 응답
```json
{
  "code": 200,
  "message": "user_updated_successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "nickname": "updated_nickname",
    "profileImage": "https://example.com/image.jpg",
    "state": "PROFILE_SETTING",
    "tendencyType": null,
    "..."
  }
}
```

---

## ✅ 검증 체크리스트

- [ ] UserState enum 파일 생성
- [ ] User 모델에서 needs_onboarding → state 변경
- [ ] UserDto 스키마 업데이트 (state, tendencyType 추가)
- [ ] 토큰 블랙리스트 시스템 추가
- [ ] CredentialDto 카멜케이스 적용
- [ ] 세션 엔드포인트 경로 수정 ("/" → "")
- [ ] 모든 API 응답 by_alias=True 적용
- [ ] 사용자 상태 결정 로직 구현
- [ ] 데이터베이스 마이그레이션 실행
- [ ] 기존 데이터 마이그레이션 스크립트 실행

---

## 🔍 테스트 명령어

```bash
# 가상환경 활성화 후 서버 실행
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API 테스트 (예시)
curl -X PUT http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"refreshToken": "your_refresh_token"}'
```

---

## 🆕 최신 업데이트 사항 (2025-09-05)

### 8. OAuth 에러 처리 개선

#### 8.1 ErrorResponse 스키마 업데이트
**파일:** `app/schemas/common.py`

```python
# 기존
class ErrorResponse(BaseModel):
    error_code: str
    status: int
    message: str

# 변경 후
class ErrorResponse(BaseModel):
    error_code: str
    status: int
    message: str = "Unknown error"  # 기본값 설정
```

#### 8.2 카카오 OAuth 서비스 개선
**파일:** `app/services/kakao_oauth_service.py`

```python
# 1. 프로필 이미지 URL 안전한 추출 (127-137줄 근처)
# 기존
oauth_user_info["image_url"] = (
    kakao_user_info.kakao_account.profile.profile_image_url
)

# 변경 후
# 프로필 이미지 URL 안전하게 추출
image_url = None
if (
    kakao_user_info.kakao_account
    and kakao_user_info.kakao_account.profile
    and kakao_user_info.kakao_account.profile.profile_image_url
):
    image_url = kakao_user_info.kakao_account.profile.profile_image_url

oauth_user_info["image_url"] = image_url

# 2. 에러 메시지 null 방지 (150-170줄 근처)
# 기존
message=params.error,

# 변경 후
message=params.error or "카카오 OAuth 인증 실패",
message=params.error or "인가 코드가 필요합니다",
```

### 9. 사용자 상태 로직 실시간 계산

#### 9.1 UserService 메서드 업데이트
**파일:** `app/services/user_service.py`

```python
# 1. _prepare_user_dto_data를 async로 변경
async def _prepare_user_dto_data(self, user) -> dict:
    """UserDto 생성을 위한 데이터 준비"""
    # 기본 사용자 정보
    user_data = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "nickname": user.nickname,
        "profile_image": user.profile_image,
        "intro": user.intro,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }

    # 실제 데이터 조회
    has_preferred_artists = await self._has_preferred_artists(user.id)
    has_tendency_result = await self._has_tendency_result(user.id)

    # 사용자 상태 결정
    user_data["state"] = self._determine_user_state(
        user, has_preferred_artists, has_tendency_result
    )

    # 성향 타입 추가
    user_data["tendency_type"] = await self._get_user_tendency_type(user.id)

    return user_data

# 2. 헬퍼 메서드들 추가
async def _has_preferred_artists(self, user_id: int) -> bool:
    """사용자가 선호 아티스트를 설정했는지 확인"""
    try:
        preferred_artists = await self.get_preferred_artists(user_id)
        return len(preferred_artists) > 0
    except:
        return False

async def _has_tendency_result(self, user_id: int) -> bool:
    """사용자가 성향 테스트를 완료했는지 확인"""
    from sqlalchemy import select
    from app.models.tendency import UserTendencyResult

    try:
        result = await self.user_crud.db.execute(
            select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
        )
        user_tendency = result.scalar_one_or_none()
        return user_tendency is not None
    except:
        return False

async def _get_user_tendency_type(self, user_id: int) -> Optional[str]:
    """사용자의 성향 타입 조회"""
    from sqlalchemy import select
    from app.models.tendency import UserTendencyResult

    try:
        result = await self.user_crud.db.execute(
            select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
        )
        user_tendency = result.scalar_one_or_none()
        if user_tendency:
            return user_tendency.tendency_type
        return None
    except:
        return None

# 3. 모든 _prepare_user_dto_data 호출을 await로 변경
# create_user, get_user_by_auth_provider_id, get_user, update_profile 메서드에서
user_data = await self._prepare_user_dto_data(user)
```

### 10. 프로필 설정 여부 자동 감지

#### 10.1 상태 결정 로직 개선
**파일:** `app/services/user_service.py`의 `_determine_user_state` 메서드

```python
def _determine_user_state(
    self, user, has_preferred_artists: bool, has_tendency_result: bool
) -> UserState:
    """사용자 온보딩 상태 결정"""
    # 1. 선호 아티스트가 없으면 PREFERRED_ARTISTS
    if not has_preferred_artists:
        return UserState.PREFERRED_ARTISTS

    # 2. 성향 테스트 결과가 없으면 TENDENCY_TEST
    if not has_tendency_result:
        return UserState.TENDENCY_TEST

    # 3. 프로필이 업데이트되지 않았으면 PROFILE_SETTING
    # 생성날짜와 업데이트 날짜를 비교하여 프로필 설정 여부 판단
    # 업데이트 날짜가 생성날짜와 같거나 거의 같으면 프로필을 설정하지 않은 것으로 간주
    if user.created_at and user.updated_at:
        # 업데이트 시간과 생성 시간의 차이가 1분 이내면 프로필 미설정으로 판단
        time_diff = (user.updated_at - user.created_at).total_seconds()
        if time_diff < 60:  # 60초 이내면 프로필 미설정
            return UserState.PROFILE_SETTING

    # 4. 모든 조건을 만족하면 COMPLETED
    return UserState.COMPLETED
```

## ⚠️ 중요 참고사항

1. **OAuth 에러 처리**: 모든 OAuth 서비스에서 동일한 패턴 적용 필요
2. **성능 최적화**: 사용자 상태 계산이 DB 조회를 포함하므로 캐싱 고려
3. **프로필 설정 기준**: 60초 기준은 프로젝트 요구사항에 맞게 조정 가능
4. **테스트**: 사용자 상태 변화 로직 철저히 테스트 필요

---

---

## 🆕 성향 테스트 DB 타입 매핑 수정 (2025-09-05)

### 9. 성향 테스트 "결과를 찾을 수 없습니다" 에러 해결

#### 9.1 문제 원인
DB에 저장된 성향 타입 형식이 일관성이 없어서 매핑 실패:

**DB 확인 결과 (수정 전):**
```sql
SELECT type FROM tendency_results;
-- 결과:
-- QUIET_MATE       (대문자 언더스코어)
-- TOGETHER_MATE    (대문자 언더스코어)
-- fieldMate        (camelCase) ❌
-- supportMate      (camelCase) ❌
-- creativeMate     (camelCase) ❌
-- pilgrimMate      (camelCase) ❌
```

**DB 수정 후:**
```sql
-- 모든 타입을 대문자 언더스코어 형식으로 통일
UPDATE tendency_results SET type = 'FIELD_MATE' WHERE type = 'fieldMate';
UPDATE tendency_results SET type = 'SUPPORT_MATE' WHERE type = 'supportMate';
UPDATE tendency_results SET type = 'CREATIVE_MATE' WHERE type = 'creativeMate';
UPDATE tendency_results SET type = 'PILGRIM_MATE' WHERE type = 'pilgrimMate';

-- 최종 결과: 모두 일관된 형식
-- QUIET_MATE, TOGETHER_MATE, FIELD_MATE, SUPPORT_MATE, CREATIVE_MATE, PILGRIM_MATE
```

#### 9.2 해결 방법
**파일:** `app/services/tendency_service.py`

```python
# 기존 (잘못된 매핑)
type_mapping = {
    "QUIET_MATE": "quietMate",
    "TOGETHER_MATE": "togetherMate",
    "FIELD_MATE": "fieldMate",
    # ...
}

# 수정 후 (DB 타입 통일 완료)
# DB의 타입이 모두 대문자 언더스코어 형식으로 통일됨
# 매핑 없이 직접 사용 (모든 타입이 UPPER_CASE 형식)
mapped_type = tendency_type
```

#### 9.3 적용 순서
1. **DB 타입 형식 확인**
   ```sql
   SELECT type, description FROM tendency_results;
   ```

2. **DB 타입 통일** (권장)
   ```sql
   -- camelCase를 대문자 언더스코어로 변경
   UPDATE tendency_results SET type = 'FIELD_MATE' WHERE type = 'fieldMate';
   UPDATE tendency_results SET type = 'SUPPORT_MATE' WHERE type = 'supportMate';
   UPDATE tendency_results SET type = 'CREATIVE_MATE' WHERE type = 'creativeMate';
   UPDATE tendency_results SET type = 'PILGRIM_MATE' WHERE type = 'pilgrimMate';
   ```

3. **코드 매핑 단순화**
   - `get_tendency_result` 메서드에서 복잡한 매핑 제거
   - 모든 타입이 일관된 형식이므로 직접 사용

4. **테스트**
   - 성향 테스트 제출 API 호출
   - 모든 성향 타입이 올바르게 조회되는지 확인

#### 9.4 ⚠️ 다른 환경 적용 시 주의사항
1. **DB 데이터 일관성**: 모든 환경에서 동일한 타입 형식 사용 권장
2. **마이그레이션**: 기존 데이터가 있다면 일관된 형식으로 통일
3. **테스트**: 각 성향 타입별로 테스트 필요

---

## 🆕 DB 스키마 업데이트 - state 컬럼 추가 (2025-09-05)

### 10. "table users has no column named state" 에러 해결

#### 10.1 문제 원인
User 모델에 `state` 컬럼을 추가했지만 실제 데이터베이스 스키마가 업데이트되지 않음:

```
sqlite3.OperationalError: table users has no column named state
[SQL: INSERT INTO users (..., state, ...) VALUES (...)]
```

#### 10.2 해결 방법

**Option 1: Alembic 마이그레이션 (권장)**
```bash
# 마이그레이션 파일 생성
alembic revision --autogenerate -m "Add state column to users table"

# 마이그레이션 적용
alembic upgrade head
```

**Option 2: 직접 SQL 실행 (빠른 해결)**
```sql
-- state 컬럼 추가
ALTER TABLE users ADD COLUMN state VARCHAR(50) DEFAULT 'PREFERRED_ARTISTS';

-- 기존 사용자 state 값 설정
UPDATE users SET state = 'PREFERRED_ARTISTS' WHERE state IS NULL;

-- 확인
PRAGMA table_info(users);
SELECT id, nickname, state FROM users;
```

#### 10.3 적용 순서
1. **현재 스키마 확인**
   ```sql
   PRAGMA table_info(users);
   ```

2. **컬럼 추가**
   ```sql
   ALTER TABLE users ADD COLUMN state VARCHAR(50) DEFAULT 'PREFERRED_ARTISTS';
   ```

3. **기존 데이터 업데이트**
   ```sql
   UPDATE users SET state = 'PREFERRED_ARTISTS' WHERE state IS NULL;
   ```

4. **확인 및 테스트**
   - 사용자 생성/조회 API 테스트
   - 새 사용자 가입 시 state 값 확인

#### 10.4 ⚠️ 다른 환경 적용 시 주의사항
1. **백업**: 프로덕션 DB는 반드시 백업 후 진행
2. **마이그레이션**: 가능하면 Alembic을 통한 정식 마이그레이션 권장
3. **기본값**: 기존 사용자들의 state 기본값 설정 확인
4. **테스트**: 사용자 관련 모든 API 동작 확인

---

이 가이드를 따라하면 다른 환경에서도 동일한 기능을 구현할 수 있습니다! 🚀
