# 데이터베이스 정보

## 환경별 접속 정보

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
