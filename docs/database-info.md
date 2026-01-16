# 데이터베이스 정보

## 환경별 설정 가이드

### Local 환경 (MySQL 직접 설치)
MySQL이 로컬에 설치되어 있는 경우 권장합니다.

```bash
# MySQL 설치 (Mac)
brew install mysql
brew services start mysql

# 데이터베이스 생성
mysql -u root -p
CREATE DATABASE podpod_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```yaml
# config.dev.yaml
database:
  host: "localhost"
  port: 3306
  name: "podpod_dev"
  user: "root"
```

### Dev 환경 (MySQL 도커)
MySQL이 설치되어 있지 않은 경우 권장합니다.

```bash
# Docker Compose로 MySQL 실행
docker-compose -f docker-compose.dev.yml up -d db

# 또는 MySQL만 단독 실행
docker run -d \
  --name podpod-mysql-dev \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=podpod_dev \
  -p 3306:3306 \
  mysql:8.0
```

### Staging
```yaml
host: localhost
port: 3306
database: podpod_staging
user: root
password: Infisical에서 관리
```

### Production
```yaml
host: localhost
port: 3306
database: podpod
user: root
password: Infisical에서 관리
```

## Redis 설정

**모든 환경에서 Docker로 실행합니다.**

```bash
# 개발 환경 Redis 실행
docker-compose -f docker-compose.dev.yml up -d redis

# 또는 Redis만 단독 실행
docker run -d \
  --name podpod-redis-dev \
  -p 6379:6379 \
  redis:7-alpine
```

용도:
- 리프레시 토큰 저장
- OAuth state 관리
- 토큰 블랙리스트

## 환경 선택 가이드

| 조건 | 권장 환경 |
|------|----------|
| MySQL 설치됨 | Local (직접 실행) |
| MySQL 미설치 | Dev (Docker) |
| 전체 스택 테스트 | Docker Compose 전체 |

## 비밀번호 관리

### 로컬/개발 환경
- `.env` 파일에 `MYSQL_PASSWORD` 설정
- Infisical 사용 시 자동으로 주입됨

### 스테이징/프로덕션 환경
- Infisical에서 중앙 관리
- 환경 변수로 자동 주입

## 마스터 데이터 관리

### 임포트
```bash
./scripts/import-master-data-local.sh  # 로컬
./scripts/import-master-data.sh        # 원격
```

### 익스포트
```bash
./scripts/export-master-data.sh
```
