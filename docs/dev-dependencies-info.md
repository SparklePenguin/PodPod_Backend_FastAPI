# 개발 의존성 가이드

## 필수 의존성

### MySQL (선택: 직접 설치 또는 Docker)

#### 옵션 1: 직접 설치 (권장 - 이미 설치된 경우)
```bash
# 설치
brew install mysql

# 시작
brew services start mysql

# 데이터베이스 생성
mysql -u root -p
CREATE DATABASE podpod_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 옵션 2: Docker (권장 - 미설치된 경우)
```bash
# Docker Compose로 실행
docker-compose -f docker-compose.dev.yml up -d db

# 상태 확인
docker ps | grep podpod-mysql
```

### Redis (Docker로 실행)
세션 및 캐시 관리용. **모든 환경에서 Docker로 실행합니다.**

```bash
# Docker Compose로 실행
docker-compose -f docker-compose.dev.yml up -d redis

# 또는 단독 실행
docker run -d --name podpod-redis-dev -p 6379:6379 redis:7-alpine

# 상태 확인
docker exec podpod-redis-dev redis-cli ping  # 응답: PONG
```

용도:
- 리프레시 토큰 저장
- OAuth state 관리
- 토큰 블랙리스트

### Infisical
환경 변수 관리 도구

```bash
# 설치
brew install infisical/get-cli/infisical

# 로그인
infisical login

# 사용: 스크립트에서 자동 실행 (infisical run)
```

### Cloudflare (클플)
- DNS 및 프록시 관리
- 도메인: `sp-podpod.com`

## 빠른 시작

### 전체 스택 실행 (Docker Compose)
```bash
# MySQL + Redis + API 전체 실행
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f api
```

### 로컬 개발 (MySQL 직접 설치 + Redis Docker)
```bash
# Redis만 Docker로 실행
docker-compose -f docker-compose.dev.yml up -d redis

# API 로컬 실행
./scripts/run-dev.sh
```

## 프로젝트 빠른 접근

### Alias 설정
```bash
echo "alias podpod='cd /Users/jogiyeol/Documents/GitHub/PodPod_Backend_FastAPI/'" >> ~/.zshrc
source ~/.zshrc
```

사용: `podpod` 입력 시 프로젝트 디렉토리로 이동

## Nginx 설정

### 설정 파일 위치
```bash
sudo vi /opt/homebrew/etc/nginx/servers/sp-podpod.conf
```

### 주요 명령어

#### 상태 확인
```bash
ps aux | grep nginx
```

#### 실행
```bash
sudo nginx  # Mac Brew Nginx 이슈로 수동 실행 중
```

#### 리로드 (실행 중일 때)
```bash
sudo nginx -s reload
```

#### 종료
```bash
sudo nginx -s quit
```

### 로그 확인

#### 에러 로그
```bash
sudo tail -f /opt/homebrew/var/log/nginx/error.log
```

#### 액세스 로그
```bash
sudo tail -f /opt/homebrew/var/log/nginx/access.log
```

## 추가 도구

### Python 환경
- **pyenv**: Python 버전 관리
- **uv**: 패키지 관리 (pip 대체)

### Docker
- 개발 환경에서 MySQL/Redis 실행에 필수
- `docker-compose -f docker-compose.dev.yml up -d`
