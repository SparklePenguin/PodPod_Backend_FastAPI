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
