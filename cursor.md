# 데이터베이스 관련 작업 시 반드시 사용할 스크립트들

## 데이터베이스 마이그레이션
- `./migrate.sh` 사용 (alembic upgrade head 실행)

## SQL 쿼리 실행
- **반드시** `./execute_sql.sh "SQL쿼리"` 사용
- 예시: `./execute_sql.sh "DESCRIBE pod_members;"`
- 예시: `./execute_sql.sh "SELECT * FROM pods LIMIT 5;"`
- **절대** `mysql -u root -p` 직접 사용 금지

## 서버 상태
- 서버는 항상 재시작 중임 (굳이 껐다 다시 킬 필요 없음)