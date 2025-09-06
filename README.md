# PodPod Backend FastAPI

소셜 로그인을 지원하는 FastAPI 백엔드 서버입니다.

## 🚀 서버 실행

### 방법 1: run 스크립트 사용 (권장)
```bash
./run
```
- 가상환경 자동 활성화
- Infisical을 통한 환경변수 로드
- 자동 리로드 활성화

### 방법 2: 가상환경이 이미 활성화된 경우
```bash
# 가상환경 활성화
source venv/bin/activate

# 서버 실행
python3 run.py
```

### 실행 옵션들

#### Infisical 없이 실행
```bash
./run --no-infisical
# 또는
python3 run.py --no-infisical
```

#### 호스트/포트 변경
```bash
./run --host 0.0.0.0 --port 3000
# 또는
python3 run.py --host 0.0.0.0 --port 3000
```

#### 자동 리로드 비활성화
```bash
./run --no-reload
# 또는
python3 run.py --no-reload
```

#### 도움말 확인
```bash
./run --help
# 또는
python3 run.py --help
```

## 📁 프로젝트 구조

```
PodPod_Backend_FastAPI/
├── app/                    # 애플리케이션 코드
│   ├── api/               # API 라우터
│   ├── core/              # 핵심 설정 (데이터베이스, 보안 등)
│   ├── crud/              # 데이터베이스 CRUD 작업
│   ├── models/            # SQLAlchemy 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── services/          # 비즈니스 로직
│   └── utils/             # 유틸리티 함수
├── alembic/               # 데이터베이스 마이그레이션
├── logs/                  # 로그 파일
├── mvp/                   # MVP 데이터 파일들
│   ├── artists.json
│   ├── tendency_results.json
│   └── tendency_test.json
├── uploads/               # 업로드된 파일
├── config.yaml            # 서버 설정 파일
├── run.py                 # 서버 실행 스크립트
├── run                    # 가상환경 자동 활성화 스크립트
└── requirements.txt       # Python 의존성
```

## ⚙️ 설정

### config.yaml
서버 설정을 `config.yaml` 파일에서 관리할 수 있습니다:

```yaml
# 서버 설정
server:
  host: "127.0.0.1"  # 서버 호스트
  port: 8000         # 서버 포트
  reload: true       # 개발 모드에서 자동 리로드

# Infisical 설정 (환경변수 관리)
infisical:
  enabled: true      # Infisical 사용 여부
  env: "dev"         # 환경 (dev, staging, prod 등)
  path: "/backend"   # Infisical에서 환경변수를 가져올 경로
```

## 🔧 개발 환경 설정

### 1. 가상환경 생성
```bash
python3 -m venv venv
```

### 2. 가상환경 활성화
```bash
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 데이터베이스 마이그레이션
```bash
alembic upgrade head
```

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 환경변수

Infisical을 통해 다음 환경변수들을 관리합니다:
- 데이터베이스 연결 정보
- OAuth 클라이언트 정보 (Google, Apple, Kakao)
- JWT 시크릿 키
- 기타 보안 관련 설정

## 📝 로그

로그 파일은 `logs/` 디렉토리에 저장됩니다:
- `app.log`: 일반 애플리케이션 로그
- `error.log`: 에러 로그

## 🛠️ 기술 스택

- **Framework**: FastAPI
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Authentication**: JWT, OAuth (Google, Apple, Kakao)
- **Environment Management**: Infisical
- **Configuration**: YAML

## 📝 Git 커밋 컨벤션

### 🎯 커밋 메시지 형식
```
<type>(<scope>): <subject>
```

### 🔹 Types (타입)
- **feat**: 새로운 기능 추가
- **fix**: 버그 수정
- **docs**: 문서 수정
- **style**: 코드 포맷팅, 세미콜론 누락 등 (기능 변경 없음)
- **refactor**: 코드 리팩토링
- **test**: 테스트 코드 추가/수정
- **chore**: 빌드 프로세스, 보조 도구 변경
- **perf**: 성능 개선
- **ci**: CI/CD 설정 변경
- **build**: 빌드 시스템 변경
- **revert**: 이전 커밋 되돌리기

### 🔹 Scopes (범위)
- **api**: API 엔드포인트
- **db**: 데이터베이스 관련
- **auth**: 인증/인가
- **user**: 사용자 관련
- **artist**: 아티스트 관련
- **tendency**: 성향 테스트 관련
- **config**: 설정 파일
- **logging**: 로깅 시스템
- **middleware**: 미들웨어
- **deps**: 의존성
- **docker**: Docker 관련
- **docs**: 문서

### 💡 Examples (예시)
```bash
feat(api): add user profile update endpoint
fix(db): resolve MySQL connection timeout issue
docs(readme): update installation instructions
refactor(auth): simplify OAuth flow
test(user): add user registration tests
chore(deps): update FastAPI to v0.104.0
```

### 📋 Subject Guidelines (제목 가이드라인)
- 50자 이내로 작성
- 첫 글자는 소문자
- 마침표로 끝내지 않음
- 명령형으로 작성 (예: "add" not "added")

### 🚀 자동화된 Git 훅
프로젝트에는 다음 Git 훅이 설정되어 있습니다:

#### 1. **prepare-commit-msg**: 자동 템플릿 제공
- `git commit` 입력 시 자동으로 커밋 메시지 템플릿이 표시됩니다
- 타입, 스코프, 예시가 포함된 가이드라인 제공

#### 2. **commit-msg**: 메시지 규칙 검증
- 커밋 메시지 형식 자동 검증
- 잘못된 형식일 경우 커밋 거부
- 경고 메시지로 개선 사항 안내

### 🔧 훅 설정 방법
```bash
# 실행 권한 부여 (이미 설정됨)
chmod +x .git/hooks/prepare-commit-msg
chmod +x .git/hooks/commit-msg

# 커밋 테스트
git add .
git commit  # 템플릿이 자동으로 표시됩니다
```

### 🎨 VSCode 통합
VSCode에서도 커밋 메시지 템플릿이 자동으로 표시됩니다:

#### **설정된 기능:**
- **Git 커밋 메시지 템플릿**: VSCode Git 패널에서 커밋 시 자동으로 템플릿 표시
- **Python 환경**: 가상환경 자동 활성화 및 Python 인터프리터 설정
- **코드 포맷팅**: Black 포맷터 자동 적용
- **린팅**: Flake8 린터 활성화
- **파일 연결**: YAML, SQL, INI 파일 자동 인식
- **검색 최적화**: 불필요한 디렉토리 제외

#### **VSCode 확장 프로그램 권장:**
- **Python**: Python 언어 지원
- **Black Formatter**: 코드 포맷팅
- **Flake8**: 코드 린팅
- **YAML**: YAML 파일 지원
- **SQL**: SQL 파일 지원
- **GitLens**: Git 기능 강화

#### **사용법:**
1. VSCode에서 프로젝트 열기
2. Source Control 패널 (Ctrl+Shift+G) 열기
3. 변경사항 스테이징 후 커밋 메시지 입력란에 템플릿이 자동 표시
4. 템플릿을 참고하여 커밋 메시지 작성
