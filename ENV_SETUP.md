# 환경 설정 가이드

PodPod Backend는 **Infisical + Config 파일 하이브리드** 방식으로 환경을 관리합니다.

## 구조

### 1. **Infisical (민감 정보)**
- DB 비밀번호
- OAuth 클라이언트 시크릿
- API 키
- JWT Secret
- Firebase/Google 서비스 계정 키

### 2. **Config 파일 (환경별 설정)**
- 데이터베이스 호스트/포트
- OAuth Redirect URI
- 로깅 레벨
- 서버 설정

---

## 환경별 Config 파일

| 파일 | 환경 | 용도 |
|------|------|------|
| `config.dev.yaml` | 개발 | 로컬 개발 환경 |
| `config.stg.yaml` | 스테이징 | 테스트 서버 |
| `config.prod.yaml` | 프로덕션 | 운영 서버 |

---

## 사용 방법

### 개발 환경 실행
```bash
./run
# 또는
./run --env dev
```

### 스테이징 환경 실행
```bash
./run --env stg
```

### 프로덕션 환경 실행
```bash
./run --env prod
```

### 커스텀 config 파일 사용
```bash
./run --config my-config.yaml
```

### 추가 옵션
```bash
# 포트 변경
./run --env dev --port 9000

# 자동 리로드 비활성화
./run --env prod --no-reload

# 호스트 변경
./run --env dev --host 0.0.0.0
```

---

## Infisical 설정

### 1. Infisical에 환경 생성
- `dev`: 개발 환경
- `stg`: 스테이징 환경
- `prod`: 프로덕션 환경

### 2. 각 환경에 민감 정보 등록
필수 환경변수:
- `MYSQL_PASSWORD`: MySQL 비밀번호
- `SECRET_KEY`: JWT 시크릿 키
- `KAKAO_CLIENT_ID`: 카카오 클라이언트 ID
- `KAKAO_CLIENT_SECRET`: 카카오 클라이언트 시크릿
- `GOOGLE_CLIENT_ID`: Google 클라이언트 ID
- `APPLE_CLIENT_ID`: Apple 클라이언트 ID
- `APPLE_TEAM_ID`: Apple 팀 ID
- `APPLE_KEY_ID`: Apple 키 ID
- `APPLE_PRIVATE_KEY`: Apple 프라이빗 키
- `SENDBIRD_APP_ID`: Sendbird 앱 ID
- `SENDBIRD_API_TOKEN`: Sendbird API 토큰
- `GOOGLE_SHEETS_ID`: Google Sheets ID
- `GOOGLE_SHEETS_CREDENTIALS`: Google Sheets 자격증명
- `FIREBASE_SERVICE_ACCOUNT_KEY`: Firebase 서비스 계정 키

### 3. Infisical CLI 설치
```bash
brew install infisical/get-cli/infisical
```

### 4. Infisical 로그인
```bash
infisical login
```

---

## Config 파일 수정

각 환경에 맞게 config 파일을 수정하세요:

### `config.dev.yaml` 예시
```yaml
environment: "development"

database:
  host: "localhost"
  port: 3306
  name: "podpod_dev"
  user: "root"

server:
  host: "127.0.0.1"
  port: 8000
  reload: true
  debug: true

oauth:
  kakao_redirect_uri: "http://localhost:3000/auth/kakao/callback"
  apple_redirect_uri: "http://localhost:3000/auth/apple/callback"

logging:
  level: "DEBUG"
```

### `config.prod.yaml` 예시
```yaml
environment: "production"

database:
  host: "production-db.example.com"
  port: 3306
  name: "podpod"
  user: "produser"

server:
  host: "0.0.0.0"
  port: 8000
  reload: false
  debug: false

oauth:
  kakao_redirect_uri: "https://api.podpod.com/auth/kakao/callback"
  apple_redirect_uri: "https://api.podpod.com/auth/apple/callback"

logging:
  level: "WARNING"
```

---

## 환경 확인

서버 시작 시 다음과 같은 로그가 출력됩니다:

```
========================================
PodPod FastAPI 서버 시작
========================================
✓ 설정 파일 로드: config.dev.yaml
✓ 가상환경이 활성화되어 있습니다.
환경: development
✓ Infisical 환경: dev
Infisical에서 환경변수를 로드하는 중...
환경 설정 완료: development
데이터베이스: localhost:3306/podpod_dev
```

---

## 주의사항

1. **민감 정보는 절대 Config 파일에 넣지 마세요**
   - ✅ Config 파일: 호스트, 포트, URI 등
   - ❌ Config 파일: 비밀번호, API 키, 시크릿

2. **Config 파일은 Git에 커밋하세요**
   - 환경별 설정을 팀원과 공유

3. **Infisical 환경을 일치시키세요**
   - `config.dev.yaml` → Infisical `dev` 환경
   - `config.prod.yaml` → Infisical `prod` 환경

4. **개인 설정은 `.local` 파일 사용**
   - `config.local.yaml` (Git에서 제외됨)

---

## 문제 해결

### Infisical 오류
```bash
❌ Infisical CLI를 찾을 수 없습니다.
```
→ `brew install infisical/get-cli/infisical`

### 설정 파일 없음
```bash
경고: 설정 파일 config.dev.yaml을 찾을 수 없습니다.
```
→ config 파일이 프로젝트 루트에 있는지 확인

### MySQL 연결 실패
```bash
MYSQL_PASSWORD 환경변수가 설정되지 않았습니다.
```
→ Infisical에 `MYSQL_PASSWORD` 등록 확인
