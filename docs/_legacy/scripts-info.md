# Scripts 가이드

## 설치

### 시스템 의존성 설치 (최초 1회)
```bash
./scripts/setup-dependencies.sh
```
- pyenv, Python, uv 설치
- MySQL 클라이언트 설치
- Docker 설치 확인

### Python 패키지 설치/업데이트
```bash
./scripts/install-packages.sh
```
- uv를 통한 패키지 설치
- 패키지 업데이트 시 실행

## 실행

### 로컬 환경
```bash
./scripts/start-local.sh
```
가상환경 자동 활성화 및 서버 실행 (8000, 8001 포트)

### Docker 개발 환경
```bash
./scripts/start-dev.sh
```
Docker Compose로 전체 스택 실행 (API, DB, Redis, Monitoring)

### 스테이징/프로덕션
```bash
./scripts/start-stg.sh   # 스테이징
./scripts/start-prod.sh  # 프로덕션
```

## 데이터 관리

### 마스터 데이터 임포트
```bash
./scripts/import-master-data-local.sh  # 로컬
./scripts/import-master-data.sh        # 원격
```

### 마스터 데이터 익스포트
```bash
./scripts/export-master-data.sh
```

## 기타

### 모니터링
```bash
./scripts/start-monitoring.sh
```
Grafana, Prometheus 시작

### Git 동기화
```bash
./scripts/sync-dev.sh   # dev 브랜치
./scripts/sync-main.sh  # main 브랜치
```

### Docker 이미지 푸시
```bash
./scripts/push-image.sh
```

## API 스크립트

### 에러 코드 Google Sheets 동기화
```bash
cd services/api
python scripts/sync_error_codes_to_sheet.py
```

`errors.json`과 Google Sheets 간 에러 코드를 동기화합니다.

**사전 요구사항:**
- Infisical CLI 설치 및 로그인 (`infisical login`)
- `/google-sheet` 경로에 다음 시크릿 설정:
  - `GOOGLE_SHEETS_ID`: 스프레드시트 ID
  - `GOOGLE_SERVICE_ACCOUNT_KEY`: 서비스 계정 JSON 키

**기능:**
- 도메인별 시트 자동 생성 (없는 경우)
- JSON → Sheets 업로드
- Sheets → JSON 다운로드 (역동기화)
- 도메인별 에러 코드 범위:
  - common: 0xxx, auth: 1xxx, oauth: 2xxx
  - users: 3xxx, pods: 4xxx, artists: 5xxx
  - tendencies: 6xxx, chat: 7xxx, follow: 8xxx
  - notifications: 9xxx, reports: 10xxx
