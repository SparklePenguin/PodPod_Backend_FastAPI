# API Endpoints

이 폴더는 FastAPI 엔드포인트들을 포함합니다.

## 엔드포인트 구조

### 1. Users (`/api/v1/users`)

#### 공개 API
- `POST /` - 사용자 생성 (회원가입)

#### 인증 필요 API
- `GET /me` - 내 프로필 조회
- `PUT /me` - 내 프로필 업데이트
- `GET /me/preferred-artists` - 내 선호 아티스트 조회
- `PUT /me/preferred-artists` - 내 선호 아티스트 업데이트

#### 내부용 API
- `GET /` - 모든 사용자 조회 ⚠️
- `GET /{user_id}` - 특정 사용자 조회 ⚠️

### 2. Sessions (`/api/v1/sessions`)

#### 공개 API
- `POST /kakao` - 카카오 로그인
- `POST /email` - 이메일 로그인
- `POST /refresh` - 토큰 갱신
- `POST /logout` - 로그아웃

### 3. Artists (`/api/v1/artists`)

#### 공개 API
- `GET /` - 아티스트 목록 조회
- `GET /{artist_id}` - 특정 아티스트 조회

#### 내부용 API
- `POST /mvp` - MVP 아티스트 생성 ⚠️

### 4. OAuths (`/api/v1/oauths`)

#### 공개 API
- `GET /kakao/callback` - 카카오 OAuth 콜백

## API 태그 분류

### 🔓 공개 API
- 인증이 필요하지 않은 API
- 누구나 접근 가능

### 🔐 인증 필요 API
- JWT 토큰이 필요한 API
- 로그인한 사용자만 접근 가능

### ⚠️ 내부용 API (internal 태그)
- 개발/테스트 목적으로만 사용되는 API
- Swagger에서 별도 섹션으로 구분
- 프로덕션에서는 접근 제한 필요

## 응답 형식

### 성공 응답
```json
{
  "code": 200,
  "message": "success_message",
  "data": {
    // 응답 데이터
  }
}
```

### 에러 응답
```json
{
  "error_code": "error_type",
  "status": 400,
  "message": "에러 메시지"
}
```

## 인증

### JWT 토큰
- `Authorization: Bearer <token>` 헤더 사용
- 액세스 토큰 만료 시간: 30분
- 리프레시 토큰 만료 시간: 7일

### OAuth
- 카카오 OAuth 지원
- 소셜 로그인 후 JWT 토큰 발급

## 에러 코드

- `validation_error`: 데이터 검증 실패
- `authentication_failed`: 인증 실패
- `user_not_found`: 사용자를 찾을 수 없음
- `artist_not_found`: 아티스트를 찾을 수 없음
- `internal_server_error`: 서버 내부 오류

## 개발 가이드

### 새 엔드포인트 추가 시
1. 적절한 태그 선택 (users, sessions, artists, oauths, internal)
2. 응답 모델 통일 (SuccessResponse, ErrorResponse)
3. 에러 처리 추가
4. Swagger 문서화 (summary, description)

### 내부용 API 추가 시
1. `tags=["internal"]` 추가
2. `summary`에 "(내부용)" 표시
3. `description`에 "⚠️ 내부용 API" 표시
4. 개발/테스트 목적임을 명시
