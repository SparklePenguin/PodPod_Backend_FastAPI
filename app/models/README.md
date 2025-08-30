# Models

이 폴더는 SQLAlchemy ORM 모델들을 포함합니다.

## 모델 구조

### 1. User (사용자)
**테이블명**: `users`

**필드**:
- `id` (Integer, Primary Key): 사용자 고유 ID
- `username` (String(50), Unique, Nullable): 사용자명
- `email` (String(100), Unique, Nullable): 이메일 주소 (소셜 로그인 시 Null 허용)
- `nickname` (String(50), Nullable): 닉네임
- `intro` (String(200), Nullable): 자기소개
- `hashed_password` (String(255), Nullable): 해시된 비밀번호 (소셜 로그인 시 Null)
- `profile_image` (String(500), Nullable): 프로필 이미지 URL
- `needs_onboarding` (Boolean, Default: True): 온보딩 필요 여부 (새 사용자는 기본적으로 온보딩 필요)
- `is_active` (Boolean, Default: True): 계정 활성화 상태
- `created_at` (DateTime): 생성 시간
- `updated_at` (DateTime): 수정 시간
- `auth_provider` (String(20), Nullable): 인증 제공자 ('kakao', 'google', 'apple', 'email')
- `auth_provider_id` (String(100), Unique, Nullable): 소셜 제공자의 고유 ID

**관계**:
- `preferred_artists`: 사용자가 선호하는 아티스트 목록 (Many-to-Many)

### 2. Artist (아티스트)
**테이블명**: `artists`

**필드**:
- `id` (Integer, Primary Key): 아티스트 고유 ID
- `name` (String(200), Not Null): 아티스트 이름
- `profile_image` (String(500), Nullable): 아티스트 프로필 이미지 URL
- `created_at` (DateTime): 생성 시간
- `updated_at` (DateTime): 수정 시간

**관계**:
- `preferred_artists`: 이 아티스트를 선호하는 사용자 목록 (Many-to-Many)

### 3. PreferredArtist (선호 아티스트 관계)
**테이블명**: `preferred_artists`

**필드**:
- `user_id` (Integer, Foreign Key): 사용자 ID
- `artist_id` (Integer, Foreign Key): 아티스트 ID
- **복합 기본키**: (user_id, artist_id)

**관계**:
- `user`: 연결된 사용자 (Many-to-One)
- `artist`: 연결된 아티스트 (Many-to-One)

## 관계 다이어그램

```
User (1) ←→ (Many) PreferredArtist (Many) ←→ (1) Artist
```

- 한 사용자는 여러 아티스트를 선호할 수 있음
- 한 아티스트는 여러 사용자에게 선호받을 수 있음
- `PreferredArtist` 테이블이 중간 테이블 역할

## 사용 예시

### 사용자 생성
```python
user = User(
    email="user@example.com",
    username="username",
    nickname="닉네임",
    auth_provider="kakao",
    auth_provider_id="12345"
)
```

### 아티스트 생성
```python
artist = Artist(
    name="방탄소년단",
    profile_image="https://example.com/bts.jpg"
)
```

### 선호 아티스트 추가
```python
preferred = PreferredArtist(
    user_id=1,
    artist_id=1
)
```

## 인덱스

### users 테이블
- `ix_users_id`: id 필드 인덱스
- `ix_users_email`: email 필드 유니크 인덱스
- `ix_users_username`: username 필드 유니크 인덱스
- `ix_users_auth_provider_id`: auth_provider_id 필드 유니크 인덱스

### artists 테이블
- `ix_artists_id`: id 필드 인덱스

## 제약조건

- `users.email`: UNIQUE (Nullable)
- `users.username`: UNIQUE
- `users.auth_provider_id`: UNIQUE
- `artists.name`: NOT NULL
- `preferred_artists`: 복합 기본키 (user_id, artist_id)
- 외래키 제약조건: `preferred_artists.user_id` → `users.id`
- 외래키 제약조건: `preferred_artists.artist_id` → `artists.id`
